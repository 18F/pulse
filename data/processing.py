###
#
# Given, in the data/output/scan/results directory:
#
# * domains.csv - federal domains, subset of .gov domain list.
#
# * inspect.csv - domain-scan, based on site-inspector
# * tls.csv - domain-scan, based on ssllabs-scan
# * analytics.csv - domain-scan, based on analytics.usa.gov data
#
###

import csv
import json
import os
import slugify
import datetime


## Input dirs, relative to this file.
this_dir = os.path.dirname(__file__)
INPUT_DOMAINS_DATA = os.path.join(this_dir, "./")
INPUT_SCAN_DATA = os.path.join(this_dir, "./output/scan/results")


###
# Main task flow.

from app import models
from app.models import Report, Domain, Agency
from app.data import LABELS


# Read in data from domains.csv, and scan data from domain-scan.
# All database operations are made in the run() method.
#
# This method blows away the database and rebuilds it from the given data.

def run(date):
  if date is None:
    date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")

  # Reset the database.
  print("Clearing the database.")
  models.clear_database()
  Report.create(date)

  # Read in domains and agencies from domains.csv.
  # Returns dicts of values ready for saving as Domain and Agency objects.
  domains, agencies = load_domain_data()

  # Read in domain-scan CSV data.
  scan_data = load_scan_data(domains)

  # Pull out a few inspect.csv fields as general domain metadata.
  for domain_name in scan_data.keys():
    inspect = scan_data[domain_name].get('inspect', None)
    if inspect is None:
      # generally means scan was on different domains.csv, but
      # invalid domains can hit this (e.g. fed.us).
      print("[%s][WARNING] No inspect data for domain!" % domain_name)

      # Remove the domain from further consideration.
      del domains[domain_name]
    else:
      # print("[%s] Updating with inspection metadata." % domain_name)
      domains[domain_name]['live'] = boolean_for(inspect['Live'])
      domains[domain_name]['redirect'] = boolean_for(inspect['Redirect'])
      domains[domain_name]['canonical'] = inspect['Canonical']

  # Save what we've got to the database so far.

  for domain_name in domains.keys():
    Domain.create(domains[domain_name])
    print("[%s] Created." % domain_name)
  for agency_name in agencies.keys():
    Agency.create(agencies[agency_name])
    # print("[%s] Created." % agency_name)


  # Calculate high-level per-domain conclusions for each report.
  domain_reports = process_domains(domains, agencies, scan_data)
  # Save them in the database.
  for report_type in domain_reports.keys():
    for domain_name in domain_reports[report_type].keys():
      print("[%s][%s] Adding report." % (report_type, domain_name))
      Domain.add_report(domain_name, report_type, domain_reports[report_type][domain_name])

  # Calculate agency-level summaries.
  update_agency_totals()

  # Create top-level summaries.
  reports = latest_reports()
  for report in reports:
    Report.update(report)

  print_report()


# Reads in input CSVs.
def load_domain_data():

  domain_map = {}
  agency_map = {}

  # TODO: get rid of domains.csv in the repo
  with open(os.path.join(INPUT_DOMAINS_DATA, "domains.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if row[0].lower().startswith("domain"):
        continue

      domain_name = row[0].lower().strip()
      domain_type = row[1].strip()
      agency_name = row[2].strip()
      agency_slug = slugify.slugify(agency_name)
      branch = branch_for(agency_name)

      # Exclude cities, counties, tribes, etc.
      if domain_type != "Federal Agency":
        continue

      # There are a few erroneously marked non-federal domains.
      if branch == "non-federal":
        continue

      if domain_name not in domain_map:
        domain_map[domain_name] = {
          'domain': domain_name,
          'agency_name': agency_name,
          'agency_slug': agency_slug,
          'branch': branch,
        }

      if agency_slug not in agency_map:
        agency_map[agency_slug] = {
          'name': agency_name,
          'slug': agency_slug,
          'branch': branch,
          'total_domains': 1
        }

      else:
        agency_map[agency_slug]['total_domains'] += 1

  return domain_map, agency_map


# Load in data from the CSVs produced by domain-scan.
# The 'domains' map is sent in to ignore untracked domains.
def load_scan_data(domains):

  scan_data = {}
  for domain_name in domains.keys():
    scan_data[domain_name] = {}

  headers = []
  with open(os.path.join(INPUT_SCAN_DATA, "inspect.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domains.get(domain):
        # print("[inspect] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell
      scan_data[domain]['inspect'] = dict_row

  headers = []
  with open(os.path.join(INPUT_SCAN_DATA, "tls.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domains.get(domain):
        # print("[tls] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell

      # For now: overwrite previous rows if present, use last endpoint.
      scan_data[domain]['tls'] = dict_row


  # Now, analytics measurement.
  headers = []
  with open(os.path.join(INPUT_SCAN_DATA, "analytics.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domains.get(domain):
        # print("[analytics] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      # If it didn't appear in the inspect data, skip it, we need this.
      # if not domains[domain].get('inspect'):
      #   print("[analytics] Skipping %s, did not appear in inspect.csv." % domain)
      #   continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell

      scan_data[domain]['analytics'] = dict_row

  return scan_data

# Given the domain data loaded in from CSVs, draw conclusions,
# and filter/transform data into form needed for display.
def process_domains(domains, agencies, scan_data):

  reports = {
    'analytics': {},
    'https': {}
  }

  # For each domain, determine eligibility and, if eligible,
  # use the scan data to draw conclusions.
  for domain_name in domains.keys():

    if eligible_for_analytics(domains[domain_name]):
      reports['analytics'][domain_name] = analytics_report_for(
        domain_name, domains[domain_name], scan_data
      )

    if eligible_for_https(domains[domain_name]):
      reports['https'][domain_name] = https_report_for(
        domain_name, domains[domain_name], scan_data
      )

  return reports

# Go through each report type and add agency totals for each type.
def update_agency_totals():
  all_agencies = Agency.all()

  # For each agency, update their report counts for every domain they have.
  for agency in all_agencies:

    # TODO: Do direct DB queries for answers, rather than iterating.

    # Analytics

    eligible = Domain.eligible_for_agency(agency['slug'], 'analytics')

    agency_report = {
      'eligible': len(eligible),
      'participating': 0
    }

    for domain in eligible:
      report = domain['analytics']
      if report['participating'] == True:
        agency_report['participating'] += 1

    print("[%s][%s] Adding report." % (agency['slug'], 'analytics'))
    Agency.add_report(agency['slug'], 'analytics', agency_report)


    # HTTPS
    eligible = Domain.eligible_for_agency(agency['slug'], 'https')

    agency_report = {
      'eligible': len(eligible),
      'uses': 0,
      'enforces': 0,
      'hsts': 0,
      'grade': 0
    }

    for domain in eligible:
      report = domain['https']

      # Needs to be enabled, with issues is allowed
      if report['uses'] >= 1:
        agency_report['uses'] += 1

      # Needs to be Default or Strict to be 'Yes'
      if report['enforces'] >= 2:
        agency_report['enforces'] += 1

      # Needs to be at least partially present
      if report['hsts'] >= 1:
        agency_report['hsts'] += 1

      # Needs to be A- or above
      if report['grade'] >= 4:
        agency_report['grade'] += 1

    print("[%s][%s] Adding report." % (agency['slug'], 'https'))
    Agency.add_report(agency['slug'], 'https', agency_report)


def eligible_for_https(domain):
  return (domain["live"] == True)

def eligible_for_analytics(domain):
  return (
    (domain["live"] == True) and
    (domain["redirect"] == False) and
    (domain["branch"] == "executive")
  )

# Analytics conclusions for a domain based on analytics domain-scan data.
def analytics_report_for(domain_name, domain, scan_data):
  analytics = scan_data[domain_name]['analytics']
  inspect = scan_data[domain_name]['inspect']

  return {
    'participating': boolean_for(analytics['Participates in Analytics'])
  }

# HTTPS conclusions for a domain based on inspect/tls domain-scan data.
def https_report_for(domain_name, domain, scan_data):
  inspect = scan_data[domain_name]['inspect']

  report = {}

  ###
  # Is it there? There for most clients? Not there?

  # assumes that HTTPS would be technically present, with or without issues
  if (inspect["Downgrades HTTPS"] == "True"):
    https = 0 # No
  else:
    if (inspect["Valid HTTPS"] == "True"):
      https = 2 # Yes
    elif (
      (inspect["HTTPS Bad Chain"] == "True") and
      (inspect["HTTPS Bad Hostname"] == "False")
    ):
      https = 1 # Yes
    else:
      https = -1 # No

  report['uses'] = https


  ###
  # Is HTTPS enforced?

  if (https <= 0):
    behavior = 0 # N/A

  else:

    # "Yes (Strict)" means HTTP immediately redirects to HTTPS,
    # *and* that HTTP eventually redirects to HTTPS.
    #
    # Since a pure redirector domain can't "default" to HTTPS
    # for itself, we'll say it "Enforces HTTPS" if it immediately
    # redirects to an HTTPS URL.
    if (
      (inspect["Strictly Forces HTTPS"] == "True") and
      (
        (inspect["Defaults to HTTPS"] == "True") or
        (inspect["Redirect"] == "True")
      )
    ):
      behavior = 3 # Yes (Strict)

    # "Yes" means HTTP eventually redirects to HTTPS.
    elif (
      (inspect["Strictly Forces HTTPS"] == "False") and
      (inspect["Defaults to HTTPS"] == "True")
    ):
      behavior = 2 # Yes

    # Either both are False, or just 'Strict Force' is True,
    # which doesn't matter on its own.
    # A "present" is better than a downgrade.
    else:
      behavior = 1 # Present (considered 'No')

  report['enforces'] = behavior


  ###
  # Characterize the presence and completeness of HSTS.

  if inspect["HSTS Max Age"]:
    hsts_age = int(inspect["HSTS Max Age"])
  else:
    hsts_age = None

  # Without HTTPS there can be no HSTS.
  if (https <= 0):
    hsts = -1 # N/A (considered 'No')

  else:

    # HTTPS is there, but no HSTS header.
    if (inspect["HSTS"] == "False"):
      hsts = 0 # No

    # HSTS preload ready already implies a minimum max-age, and
    # may be fine on the root even if the canonical www is weak.
    elif (inspect["HSTS Preload Ready"] == "True"):

      if inspect["HSTS Preloaded"] == "True":
        hsts = 4 # Yes, and preloaded
      else:
        hsts = 3 # Yes, and preload-ready

    # We'll make a judgment call here.
    #
    # The OMB policy wants a 1 year max-age (31536000).
    # The HSTS preload list wants an 18 week max-age (10886400).
    #
    # We don't want to punish preload-ready domains that are between
    # the two.
    #
    # So if you're below 18 weeks, that's a No.
    # If you're between 18 weeks and 1 year, it's a Yes
    # (but you'll get a warning in the extended text).
    # 1 year and up is a yes.
    elif (hsts_age < 10886400):
      hsts = 0 # No, too weak

    else:
      # This kind of "Partial" means `includeSubdomains`, but no `preload`.
      if (inspect["HSTS All Subdomains"] == "True"):
        hsts = 2 # Yes

      # This kind of "Partial" means HSTS, but not on subdomains.
      else: # if (inspect["HSTS"] == "True"):

        hsts = 1 # Yes

  report['hsts'] = hsts
  report['hsts_age'] = hsts_age


  ###
  # Include the SSL Labs grade for a domain.

  # We may not have gotten any scan data from SSL Labs - it happens.
  tls = scan_data[domain_name].get('tls', None)

  fs = None
  sig = None
  ssl3 = None
  tls12 = None
  rc4 = None

  # Not relevant if no HTTPS
  if (https <= 0):
    grade = -1 # N/A

  elif tls is None:
    # print("[https][%s] No TLS scan data found." % domain)
    grade = -1 # N/A

  else:

    grade = {
      "F": 0,
      "T": 1,
      "C": 2,
      "B": 3,
      "A-": 4,
      "A": 5,
      "A+": 6
    }[tls["Grade"]]

    ###
    # Construct a sentence about the domain's TLS config.
    #
    # Consider SHA-1, FS, SSLv3, and TLSv1.2 data.

    fs = int(tls["Forward Secrecy"])
    sig = tls["Signature Algorithm"]
    rc4 = boolean_for(tls["RC4"])
    ssl3 = boolean_for(tls["SSLv3"])
    tls12 = boolean_for(tls["TLSv1.2"])

  report['grade'] = grade

  report['fs'] = fs
  report['sig'] = sig
  report['rc4'] = rc4
  report['ssl3'] = ssl3
  report['tls12'] = tls12

  return report


# Create a Report about each tracked stat.
def latest_reports():

  https_domains = Domain.eligible('https')

  total = len(https_domains)
  uses = 0
  enforces = 0
  hsts = 0
  for domain in https_domains:
    report = domain['https']
    # HTTPS needs to be enabled.
    # It's okay if it has a bad chain.
    # However, it's not okay if HTTPS is downgraded.
    if (
      (report['uses'] >= 1) and
      (report['enforces'] >= 1)
    ):
      uses += 1

    # Needs to be Default or Strict to be 'Yes'
    if report['enforces'] >= 2:
      enforces += 1

    # Needs to be at least partially present
    if report['hsts'] >= 1:
      hsts += 1

  https_report = {
    'https': {
      'eligible': total,
      'uses': uses,
      'enforces': enforces,
      'hsts': hsts
    }
  }

  analytics_domains = Domain.eligible('analytics')
  total = len(analytics_domains)
  participating = 0
  for domain in analytics_domains:
    report = domain['analytics']
    if report['participating'] == True:
      participating += 1

  analytics_report = {
    'analytics': {
      'eligible': total,
      'participating': participating
    }
  }

  return [https_report, analytics_report]

# Hacky helper - print out the %'s after the command finishes.
def print_report():
  print()

  report = Report.latest()
  for report_type in report.keys():
    if report_type == "report_date":
      continue

    print("[%s]" % report_type)
    eligible = report[report_type]["eligible"]
    for key in report[report_type].keys():
      if key == "eligible":
        continue
      print("%s: %i" % (key, percent(report[report_type][key], eligible)))
    print()



### utilities

def percent(num, denom):
  return round((num / denom) * 100)


def boolean_for(string):
  if string == "False":
    return False
  else:
    return True

def branch_for(agency):
  if agency in [
    "Library of Congress",
    "The Legislative Branch (Congress)",
    "Government Printing Office",
    "Congressional Office of Compliance"
  ]:
    return "legislative"

  if agency in ["The Judicial Branch (Courts)"]:
    return "judicial"

  if agency in ["Non-Federal Agency"]:
    return "non-federal"

  else:
    return "executive"

### Run when executed.

if __name__ == '__main__':
    run(None)
