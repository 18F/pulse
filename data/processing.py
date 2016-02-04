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


## Input and output dirs, relative to this file.
this_dir = os.path.dirname(__file__)
INPUT_DOMAINS_DATA = os.path.join(this_dir, "./")
INPUT_SCAN_DATA = os.path.join(this_dir, "./output/scan/results")


###
# Main task flow.

from app import models
from app.models import Report, Domain, Agency
from app.data import LABELS, CSV_HTTPS_DOMAINS, CSV_DAP_DOMAINS
from app.data import CSV_DAP_MAPPING, CSV_HTTPS_MAPPING


# Read in data from domains.csv, and scan data from domain-scan.
# All database operations are made in the run() method.
#
# This method blows away the database and rebuilds it from the given data.

def run(date):
  if date is None:
    date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")

  # Reset the database.
  # print("Clearing the database.")
  # models.clear_database()
  # Report.create(date)

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
      domains[domain_name]['canonical'] = boolean_for(inspect['Canonical'])

  # Save what we've got to the database so far.

  # for domain_name in domains.keys():
  #   Domain.create(domains[domain_name])
  #   print("[%s] Created." % domain_name)
  # for agency_name in agencies.keys():
  #   Agency.create(agencies[agency_name])
  #   # print("[%s] Created." % agency_name)


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
    print(report)
    Report.update(report)



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
    agency_report = {
      'eligible': len(eligible),
      'participating': 0
    }
    eligible = Domain.eligible_for_agency(agency['slug'], 'analytics')
    for domain in eligible:
      report = domain['analytics']
      if report['participating'] == True:
        agency_report['participating'] += 1

    agency_report['participating'] = percent(
      agency_report['participating'],
      agency_report['eligible']
    )

    Agency.add_report(agency['slug'], 'analytics', {
      'eligible': agency_report['eligible'],
      'participating': percent(agency_report['participating'], agency_report['eligible'])
    })


    # HTTPS
    eligible = Domain.eligible_for_agency(agency['slug'], 'https')

    agency_report = {
      'eligible': len(eligible)
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

    Agency.add_report(
      agency['slug'], 'https', {
        'eligible': len(eligible),
        'participating': analytics_participating
      }
    )



      #   if row[LABELS['https']
      #     https_stats['uses'] += 1


      if row[LABELS['https']['enforces']] >= 2:
        https_stats['enforces'] += 1

      #   # Needs to be at least partially present
      #   if row[LABELS['https']['hsts']] >= 1:
      #     https_stats['hsts'] += 1

      #   # Needs to be A- or above
      #   if row[LABELS['https']['grade']] >= 4:
      #     https_stats['grade'] += 1

      # if eligible_for_analytics(domain):

      #   analytics_total += 1
      #   row = analytics_row_for(domain)

      #   # Enabled ('Yes')
      #   if row[LABELS['analytics']['participating']] >= 1:
      #     analytics_stats['participating'] += 1


    # if https_total > 0:
    #   row = {
    #     LABELS['agency']: agency_map[agency_slug]['agency'],
    #     LABELS['total_domains']: https_total,
    #     LABELS['https']['uses']: percent(https_stats['uses'], https_total),
    #     LABELS['https']['enforces']: percent(https_stats['enforces'], https_total),
    #     LABELS['https']['hsts']: percent(https_stats['hsts'], https_total),
    #     LABELS['https']['grade_agencies']: percent(https_stats['grade'], https_total)
    #   }
    #   agency_map[agency_slug]['https'] = row
    # else:
    #   agency_map[agency_slug]['https'] = None

    # if analytics_total > 0:
    #   row = {
    #     LABELS['agency']: agency,
    #     LABELS['total_domains']: analytics_total,
    #     LABELS['analytics']['participating']: percent(analytics_stats['participating'], analytics_total)
    #   }
    #   agency_map[agency_slug]['analytics'] = row
    # else:
    #   agency_map[agency_slug]['analytics'] = None


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
      'uses': percent(uses, total),
      'enforces': percent(enforces, total),
      'hsts': percent(hsts, total)
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
      'participating': percent(participating, total)
    }
  }

  return [https_report, analytics_report]


# Given the rows we've made, save them to disk.
# def save_tables():
#   https_path = os.path.join(TABLE_DATA, "https/domains.json")
#   https_data = json_for({'data': https_domains})
#   write(https_data, https_path)


#   header_row = []
#   for label in CSV_COMMON:
#     header_row.append(LABELS[label])
#   for label in CSV_HTTPS_DOMAINS:
#     header_tow.append(LABELS['https'][label])

#   csv_https_rows = [header_row]
#   for domain in https_domains:
#     row = []
#     for label in CSV_HTTPS_DOMAINS:
#       cell = str(domain[LABELS[label]])

#       # If we have a display mapping of e.g. 1 -> "Yes", run it.
#       # This is synced manually with the JS mapping, which is bad.
#       if CSV_HTTPS_MAPPING.get(label):
#         cell = CSV_HTTPS_MAPPING[label][cell]

#       row.append(cell)
#     csv_https_rows.append(row)
#   save_csv(csv_https_rows, TABLE_DATA, "https/https-domains.csv")

#   header_row = []
#   for label in CSV_COMMON:
#     header_row.append(LABELS[label])
#   for label in CSV_DAP_DOMAINS:
#     header_row.append(LABELS['analytics'][label])

#   csv_dap_rows = [header_row]
#   for domain in analytics_domains:
#     row = []
#     for label in CSV_DAP_DOMAINS:
#       cell = str(domain[LABELS[label]])

#       # If we have a display mapping of e.g. 1 -> "Yes", run it.
#       # This is synced manually with the JS mapping, which is bad.
#       if CSV_DAP_MAPPING.get(label):
#         cell = CSV_DAP_MAPPING[label][cell]

#       row.append(cell)

#     csv_dap_rows.append(row)
#   save_csv(csv_dap_rows, TABLE_DATA, "analytics/analytics-domains.csv")

#   https_agencies_path = os.path.join(TABLE_DATA, "https/agencies.json")
#   https_agencies_data = json_for({'data': https_agencies})
#   write(https_agencies_data, https_agencies_path)

#   analytics_path = os.path.join(TABLE_DATA, "analytics/domains.json")
#   analytics_data = json_for({'data': analytics_domains})
#   write(analytics_data, analytics_path)

#   analytics_agencies_path = os.path.join(TABLE_DATA, "analytics/agencies.json")
#   analytics_agencies_data = json_for({'data': analytics_agencies})
#   write(analytics_agencies_data, analytics_agencies_path)


def save_csv(rows, directory, filename):
  full_output = os.path.join(directory, filename)
  os.makedirs(os.path.dirname(full_output), exist_ok=True)
  f = open(os.path.join(directory, filename), 'w', newline='')
  writer = csv.writer(f)
  for row in rows:
    writer.writerow(row)
  f.close()


### utilities

def percent(num, denom):
  return round((num / denom) * 100)

def boolean_nice(value):
  if value == "True":
    return 1
  elif value == "False":
    return 0
  else:
    return -1

def boolean_yes(value):
  return {
    "True": "Yes",
    "False": "No",
    "": ""
  }[value]


def boolean_for(string):
  if string == "False":
    return False
  else:
    return True

def json_for(object):
  return json.dumps(object, sort_keys=True,
                    indent=2, default=format_datetime)

def format_datetime(obj):
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    elif isinstance(obj, str):
        return obj
    else:
        return None


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

def write(content, destination):
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    f = open(destination, 'w', encoding='utf-8')
    f.write(content)
    f.close()


### Run when executed.

if __name__ == '__main__':
    run(None)
