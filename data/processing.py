###
#
# Given, in the data/output/parents/results directory:
#
# * pshtt.csv - domain-scan, based on pshtt
# * analytics.csv - domain-scan, based on analytics.usa.gov data
# * a11y.csv (optional) - pa11y scan data
# * third_parties.csv (optional) - third party scan data
#
# And, in the data/output/all directory:
#
# * gather/results/gathered.csv - all gathered .gov hostnames
# * scan/results/pshtt.csv - pshtt scan for all hostnames
# * scan/results/sslyze.csv - sslyze scan for live/TLS hostnames
#
###

import errno
import logging
import csv
import json
import yaml
import os
import glob
import slugify
import datetime
import subprocess

# Import all the constants from data/env.py.
from data.env import *

from statistics import mean

this_dir = os.path.dirname(__file__)

# domains.csv is downloaded and live-cached during the scan
PARENT_RESULTS = os.path.join(PARENTS_DATA, "./results")
PARENT_CACHE = os.path.join(PARENTS_DATA, "./cache")
PARENT_DOMAINS_CSV = os.path.join(PARENT_CACHE, "domains.csv")

# Base directory for scanned subdomain data.
ALL_DATA_AGENCIES = os.path.join(ALL_DATA, "./agencies")
ALL_DOMAINS_CSV = os.path.join(ALL_DATA_GATHERED, "results", "gathered.csv")

A11Y_ERRORS = {
  '1_1': 'Missing Image Descriptions',
  '1_3': 'Form - Initial Findings',
  '1_4': 'Color Contrast - Initial Findings',
  '4_1': 'HTML Attribute - Initial Findings'
}

CUSTOMER_SATISFACTION_TOOLS = {
    'iperceptions01.azureedge.net': 'iPerceptions',
    'ips-invite.iperceptions.com': 'iPerceptions',
    'universal.iperceptions.com': 'iPerceptions',
    'api.iperceptions.com': 'iPerceptions',
    'health.foresee.com': 'Foresee',
    'events.foreseeresults.com': 'Foresee',
    'script.hotjar.com': 'Hotjar',
    'static.hotjar.com': 'Hotjar',
    'vars.hotjar.com': 'Hotjar',
    'js.hs-analytics.net': 'HHS Voice of Customer Tool',
    'api.mixpanel.com': 'Mixpanel',
    'siteintercept.qualtrics.com': 'Qualtrics',
    'assets01.surveymonkey.com': 'SurveyMonkey',
    'secure.surveymonkey.com': 'SurveyMonkey',
    'by2.uservoice.com': 'UserVoice'
}

CUSTOMER_SATISFACTION_URLS = {
    'iPerceptions': 'https://www.iperceptions.com',
    'Foresee': 'https://www.foresee.com',
    'Hotjar': 'https://www.hotjar.com',
    'HHS Voice of Customer Tool': 'https://www.hhs.gov',
    'Mixpanel': 'https://mixpanel.com',
    'Qualtrics': 'https://www.qualtrics.com',
    'SurveyMonkey': 'https://www.surveymonkey.com',
    'UserVoice': 'https://www.uservoice.com'
}

###
# Main task flow.

from app import models
from app.models import Report, Domain, Agency
from app.data import LABELS


# Read in data from domains.csv, and scan data from domain-scan.
# All database operations are made in the run() method.
#
# This method blows away the database and rebuilds it from the given data.

# options (for debugging)

def run(date, options):
  if date is None:
    date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")

  # Reset the database.
  print("Clearing the database.")
  models.clear_database()
  Report.create(date)

  # Read in domains and agencies from domains.csv.
  # Returns dicts of values ready for saving as Domain and Agency objects.
  #
  # Also returns gathered subdomains, which need more filtering to be useful.
  domains, agencies, gathered_subdomains = load_domain_data()

  # Read in domain-scan CSV data.
  parent_scan_data = load_parent_scan_data(domains)
  subdomains, subdomain_scan_data = load_subdomain_scan_data(domains, parent_scan_data, gathered_subdomains)

  # Load in some manual exclusion data.
  analytics_ineligible = yaml.safe_load(open(os.path.join(this_dir, "ineligible/analytics.yml")))
  analytics_ineligible_map = {}
  for domain in analytics_ineligible:
    analytics_ineligible_map[domain] = True

  # Capture manual exclusions and pull out some high-level data from pshtt.
  for domain_name in parent_scan_data.keys():

    # mark manual ineligiblity for analytics if present
    analytics = parent_scan_data[domain_name].get('analytics', None)
    if analytics:
      ineligible = analytics_ineligible_map.get(domain_name, False)
      domains[domain_name]['exclude']['analytics'] = ineligible

    # Pull out a few pshtt.csv fields as general domain-level metadata.
    pshtt = parent_scan_data[domain_name].get('pshtt', None)
    if pshtt is None:
      # generally means scan was on different domains.csv, but
      # invalid domains can hit this.
      print("[%s][WARNING] No pshtt data for domain!" % domain_name)

      # Remove the domain from further consideration.
      # Destructive, so have this done last.
      del domains[domain_name]
    else:
      # print("[%s] Updating with pshtt metadata." % domain_name)
      domains[domain_name]['live'] = boolean_for(pshtt['Live'])
      domains[domain_name]['redirect'] = boolean_for(pshtt['Redirect'])
      domains[domain_name]['canonical'] = pshtt['Canonical URL']

  # Prepare subdomains the same way
  for subdomain_name in subdomain_scan_data.keys():
    pshtt = subdomain_scan_data[subdomain_name].get('pshtt')
    subdomains[subdomain_name]['live'] = boolean_for(pshtt['Live'])
    subdomains[subdomain_name]['redirect'] = boolean_for(pshtt['Redirect'])
    subdomains[subdomain_name]['canonical'] = pshtt['Canonical URL']

  # Save what we've got to the database so far.

  sorted_domains = list(domains.keys())
  sorted_domains.sort()
  sorted_subdomains = list(subdomains.keys())
  sorted_subdomains.sort()
  sorted_agencies = list(agencies.keys())
  sorted_agencies.sort()

  print("Creating all domains.")
  Domain.create_all(domains[domain_name] for domain_name in sorted_domains)
  print("Creating all subdomains.")
  Domain.create_all(subdomains[subdomain_name] for subdomain_name in sorted_subdomains)
  print("Creating all agencies.")
  Agency.create_all(agencies[agency_name] for agency_name in sorted_agencies)

  exit(1)

  # Calculate high-level per-domain conclusions for each report.
  domain_reports, subdomain_reports = process_domains(domains, subdomains, agencies, parent_scan_data, subdomain_scan_data)

  # Convenience: write out full subdomain reports, including sources
  # - CSVs per-agency
  # - One big CSV for everything
  save_subdomain_reports(subdomain_reports)

  # Save them in the database.
  sorted_types = list(domain_reports.keys())
  sorted_types.sort()
  for report_type in sorted_types:

    sorted_reports = list(domain_reports[report_type].keys())
    sorted_reports.sort()

    for domain_name in sorted_reports:
      print("[%s][%s] Adding report." % (report_type, domain_name))
      Domain.add_report(domain_name, report_type, domain_reports[report_type][domain_name])

  # Calculate agency-level summaries.
  update_agency_totals()

  # Create top-level summaries.
  reports = latest_reports()
  for report in reports:
    Report.update(report)

  print_report()


# Reads in input CSVs (domain list).
def load_domain_data():

  domain_map = {}
  agency_map = {}
  gathered_subdomain_map = {}

  # if domains.csv wasn't cached, download it anew

  if not os.path.exists(PARENT_DOMAINS_CSV):
    print("Downloading domains.csv...")
    mkdir_p(PARENT_CACHE)
    shell_out(["wget", DOMAINS, "-O", PARENT_DOMAINS_CSV])

  if not os.path.exists(PARENT_DOMAINS_CSV):
    print("Couldn't download domains.csv")
    exit(1)

  with open(PARENT_DOMAINS_CSV, newline='') as csvfile:
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
          'is_parent': True,
          'exclude': {}
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

  with open(ALL_DOMAINS_CSV, newline='') as csvfile:
    for row in csv.reader(csvfile):
      if row[0].lower().startswith("domain"):
        continue

      subdomain_name = row[0].lower().strip()
      base_domain = row[1].lower().strip()

      if subdomain_name not in gathered_subdomain_map:
        # check each source
        sources = []
        for i, source in enumerate(GATHERER_NAMES):
          if boolean_for(row[i+2]):
            sources.append(source)

        gathered_subdomain_map[subdomain_name] = sources


  return domain_map, agency_map, gathered_subdomain_map


# Load in data from the CSVs produced by domain-scan.
# The 'domains' map is used to ignore any untracked domains.
def load_parent_scan_data(domains):

  parent_scan_data = {}
  for domain_name in domains.keys():
    parent_scan_data[domain_name] = {}

  headers = []
  with open(os.path.join(PARENT_RESULTS, "pshtt.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domains.get(domain):
        print("[pshtt] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell
      parent_scan_data[domain]['pshtt'] = dict_row

  # Now, analytics measurement.

  headers = []
  with open(os.path.join(PARENT_RESULTS, "analytics.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domains.get(domain):
        # print("[analytics] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      # If it didn't appear in the pshtt data, skip it, we need this.
      # if not domains[domain].get('pshtt'):
      #   print("[analytics] Skipping %s, did not appear in pshtt.csv." % domain)
      #   continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell

      parent_scan_data[domain]['analytics'] = dict_row

  # And a11y! Only try to load it if it exists, since scan is not yet automated.
  if os.path.isfile(os.path.join(PARENT_RESULTS, "a11y.csv")):
    headers = []
    with open(os.path.join(PARENT_RESULTS, "a11y.csv"), newline='') as csvfile:
      for row in csv.reader(csvfile):
        if (row[0].lower() == "domain"):
          headers = row
          continue

        domain = row[0].lower()
        if not domains.get(domain):
          continue

        dict_row = {}
        for i, cell in enumerate(row):
          dict_row[headers[i]] = cell
        if not parent_scan_data[domain].get('a11y'):
          parent_scan_data[domain]['a11y'] = [dict_row]
        else:
          parent_scan_data[domain]['a11y'].append(dict_row)

  # Customer satisfaction, as well. Same as a11y, only load if it exists
  if os.path.isfile(os.path.join(PARENT_RESULTS, "third_parties.csv")):
    headers = []
    with open(os.path.join(PARENT_RESULTS, "third_parties.csv"), newline='') as csvfile:
      for row in csv.reader(csvfile):
        if (row[0].lower() == "domain"):
          headers = row
          continue

        domain = row[0].lower()
        if not domains.get(domain):
          continue

        dict_row = {}
        for i, cell in enumerate(row):
          dict_row[headers[i]] = cell

        parent_scan_data[domain]['cust_sat'] = dict_row

  return parent_scan_data


def load_subdomain_scan_data(domains, parent_scan_data, gathered_subdomains):

  # we'll only create entries if they are in pshtt and "live"
  subdomain_scan_data = {}

  # These will be entries in the Domain table.
  subdomains = {}

  # Next, load in subdomain pshtt data. While we also scan subdomains
  # for sslyze, pshtt is the data backbone for subdomains.
  pshtt_subdomains_csv = os.path.join(ALL_DATA_SCANNED, "results", "pshtt.csv")

  headers = []
  with open(pshtt_subdomains_csv, newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      subdomain = row[0].lower()
      parent_domain = row[1].lower()

      if subdomain not in gathered_subdomains:
        # print("[%s] Skipping, not a gathered subdomain." % subdomain)
        continue

      if not domains.get(parent_domain):
        # print("[%s] Skipping, not a subdomain of a tracked domain." % (subdomain))
        continue

      if domains[parent_domain]['branch'] != 'executive':
        # print("[%s] Skipping, not displaying data on subdomains of legislative or judicial domains." % (subdomain))
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell

      # Optimization: only bother storing in memory if Live is True.
      if boolean_for(dict_row['Live']):

        # Initialize subdomains obj if this is its first one.
        if parent_scan_data[parent_domain].get('subdomains') is None:
          parent_scan_data[parent_domain]['subdomains'] = []

        parent_scan_data[parent_domain]['subdomains'].append(subdomain)

        # if there are dupes for some reason, they'll be overwritten
        subdomain_scan_data[subdomain] = {'pshtt': dict_row}

        subdomains[subdomain] = {
          'domain': subdomain,
          'parent_domain': parent_domain,
          'agency_slug': domains[parent_domain]['agency_slug'],
          'is_parent': False,
          'sources': gathered_subdomains[subdomain]
        }

  # Load in sslyze subdomain data.
  # Note: if we ever add more subdomain scanners, this loop
  # could be genericized and iterated over really easily.
  sslyze_subdomains_csv = os.path.join(ALL_DATA_SCANNED, "results", "sslyze.csv")

  headers = []
  with open(sslyze_subdomains_csv, newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      subdomain = row[0].lower()

      if not subdomain_scan_data.get(subdomain):
        # print("[%s] Skipping, we didn't save pshtt data for this." % (subdomain))
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell

      # if there are dupes for some reason, they'll be overwritten
      subdomain_scan_data[subdomain]['sslyze'] = dict_row


  return subdomains, subdomain_scan_data

# Given the domain data loaded in from CSVs, draw conclusions,
# and filter/transform data into form needed for display.
def process_domains(domains, agencies, subdomains, parent_scan_data, subdomain_scan_data):

  reports = {
    # includes ample subdomain data
    'https': {},

    # focused on parent domains only
    'analytics': {},
    'a11y': {},
    'cust_sat': {}
  }

  # Used to generate per-agency rolled-up subdomain downloads.
  subdomain_reports = {
    'https': {}
  }

  # For each domain, determine eligibility and, if eligible,
  # use the scan data to draw conclusions.
  for domain_name in domains.keys():

    if eligible_for_analytics(domains[domain_name]):
      reports['analytics'][domain_name] = analytics_report_for(
        domain_name, domains[domain_name], parent_scan_data
      )

    if eligible_for_https(domains[domain_name]):
      reports['https'][domain_name] = https_report_for(
        domain_name, domains[domain_name], parent_scan_data, subdomain_reports
      )

    if eligible_for_a11y(domains[domain_name]):
      reports['a11y'][domain_name] = a11y_report_for(
        domain_name, domains[domain_name], parent_scan_data
      )

    if eligible_for_cust_sat(domains[domain_name]):
      reports['cust_sat'][domain_name] = cust_sat_report_for(
        domain_name, domains[domain_name], parent_scan_data
      )

  return reports, subdomain_reports

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
    eligible_https = list(map(lambda w: w['https'], eligible))
    agency_report = total_https_report(eligible_https)
    # agency_report['subdomains'] = total_https_subdomain_report(eligible)

    print("[%s][%s] Adding report." % (agency['slug'], 'https'))
    Agency.add_report(agency['slug'], 'https', agency_report)


    # A11Y
    eligible = Domain.eligible_for_agency(agency['slug'], 'a11y')
    pages_count = len(eligible)
    errors = {e:0 for e in A11Y_ERRORS.values()}
    for domain in eligible:
      a11y = domain['a11y']
      for error in a11y['errorlist']:
        errors[error] += a11y['errorlist'][error]
    total_errors = sum(errors.values())
    avg_errors_per_page = (
      'n/a' if pages_count == 0 else round(float(total_errors) / pages_count, 2)
    )
    agency_report = {
      'pages_count': pages_count,
      'eligible': pages_count,
      'Average Errors per Page': avg_errors_per_page
    }
    if pages_count:
      averages = ({
        e: round(mean([d['a11y']['errorlist'][e] for d in eligible]), 2)
        for e in A11Y_ERRORS.values()
      })
    else:
      averages = {e: 'n/a' for e in A11Y_ERRORS.values()}
    agency_report.update(averages)

    print("[%s][%s] Adding report." % (agency['slug'], 'a11y'))
    Agency.add_report(agency['slug'], 'a11y', agency_report)



    # Customer satisfaction
    eligible = Domain.eligible_for_agency(agency['slug'], 'cust_sat')
    agency_report = {
      'eligible': len(eligible),
      'participating': 0
    }
    agency_report['participating'] += len([d for d in eligible if
                                           d['cust_sat']['participating']])
    print("[%s][%s] Adding report." % (agency['slug'], 'cust_sat'))
    Agency.add_report(agency['slug'], 'cust_sat', agency_report)


# TODO: A domain can also be eligible if it has eligible subdomains.
#       Has display ramifications.
def eligible_for_https(domain):
  return (domain["live"] == True)

def eligible_for_analytics(domain):
  return (
    (domain["live"] == True) and
    (domain["redirect"] == False) and
    (domain["branch"] == "executive") and
    # managed in data/ineligible/analytics.yml
    (domain["exclude"]["analytics"] == False)
  )

def eligible_for_a11y(domain):
  return (
    (domain["live"] == True) and
    (domain["redirect"] == False) and
    (domain["branch"] == "executive")
  )

def eligible_for_cust_sat(domain):
  return (
    (domain["live"] == True) and
    (domain["redirect"] == False) and
    (domain["branch"] == "executive")
  )

# Analytics conclusions for a domain based on analytics domain-scan data.
def analytics_report_for(domain_name, domain, parent_scan_data):
  analytics = parent_scan_data[domain_name]['analytics']
  pshtt = parent_scan_data[domain_name]['pshtt']

  return {
    'participating': boolean_for(analytics['Participates in Analytics'])
  }

def a11y_report_for(domain_name, domain, parent_scan_data):
  a11y_report = {
    'errors': 0,
    'errorlist': {e:0 for e in A11Y_ERRORS.values()},
    'error_details': {e:[] for e in A11Y_ERRORS.values()}
  }
  if parent_scan_data[domain_name].get('a11y'):
    a11y = parent_scan_data[domain_name]['a11y']
    for error in a11y:
      if not error['code']:
        continue
      a11y_report['errors'] += 1
      category = get_a11y_error_category(error['code'])
      a11y_report['errorlist'][category] += 1
      details = {k: error[k] for k in ['code', 'typeCode', 'message',
                                        'context', 'selector']}
      a11y_report['error_details'][category].append(details)
  return a11y_report

def get_a11y_error_category(code):
  error_id = code.split('.')[2].split('Guideline')[1]
  return A11Y_ERRORS.get(error_id, 'Other Errors')

def cust_sat_report_for(domain_name, domain, parent_scan_data):
  cust_sat_report = {
    'service_list': {},
    'participating': False
  }
  if parent_scan_data[domain_name].get('cust_sat'):
    cust_sat = parent_scan_data[domain_name]['cust_sat']
    print(cust_sat)
    externals = [d.strip() for d in cust_sat['All External Domains'].split(',')]
    cust_sat_tools = [CUSTOMER_SATISFACTION_TOOLS[x] for
                      x in externals if
                      x in CUSTOMER_SATISFACTION_TOOLS]
    cust_sat_report['service_list'] = {s:CUSTOMER_SATISFACTION_URLS[s] for
                                     s in cust_sat_tools}
    cust_sat_report['participating'] = len(cust_sat_tools) > 0

  return cust_sat_report

# Given a pshtt report, fill in a dict with the conclusions.
def https_behavior_for(pshtt):
  report = {}

  # assumes that HTTPS would be technically present, with or without issues
  if (pshtt["Downgrades HTTPS"] == "True"):
    https = 0 # No
  else:
    if (pshtt["Valid HTTPS"] == "True"):
      https = 2 # Yes
    elif (
      (pshtt["HTTPS Bad Chain"] == "True") and
      (pshtt["HTTPS Bad Hostname"] == "False")
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
      (pshtt["Strictly Forces HTTPS"] == "True") and
      (
        (pshtt["Defaults to HTTPS"] == "True") or
        (pshtt["Redirect"] == "True")
      )
    ):
      behavior = 3 # Yes (Strict)

    # "Yes" means HTTP eventually redirects to HTTPS.
    elif (
      (pshtt["Strictly Forces HTTPS"] == "False") and
      (pshtt["Defaults to HTTPS"] == "True")
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

  if pshtt["HSTS Max Age"]:
    hsts_age = int(pshtt["HSTS Max Age"])
  else:
    hsts_age = None

  # Without HTTPS there can be no HSTS.
  if (https <= 0):
    hsts = -1  # N/A (considered 'No')

  else:

    # HSTS is present for the canonical endpoint.
    if (pshtt["HSTS"] == "True") and hsts_age:

      # Say No for too-short max-age's, and note in the extended details.
      if hsts_age >= 31536000:
        hsts = 2  # Yes
      else:
        hsts = 1  # No

    else:
      hsts = 0  # No

  # Separate preload status from HSTS status:
  #
  # * Domains can be preloaded through manual overrides.
  # * Confusing to mix an endpoint-level decision with a domain-level decision.
  if pshtt["HSTS Preloaded"] == "True":
    preloaded = 2  # Yes
  elif (pshtt["HSTS Preload Ready"] == "True"):
    preloaded = 1  # Ready for submission
  else:
    preloaded = 0  # No

  report['hsts'] = hsts
  report['hsts_age'] = hsts_age
  report['preloaded'] = preloaded

  return report

# 'eligible' should be a list of dicts with https report data.
def total_https_report(eligible):
  total_report = {
    'eligible': len(eligible),
    'uses': 0,
    'enforces': 0,
    'hsts': 0,
    'grade': 0
  }

  for report in eligible:

    # Needs to be enabled, with issues is allowed
    if report['uses'] >= 1:
      total_report['uses'] += 1

    # Needs to be Default or Strict to be 'Yes'
    if report['enforces'] >= 2:
      total_report['enforces'] += 1

    # Needs to be present with >= 1 year max-age for canonical endpoint
    if report['hsts'] >= 2:
      total_report['hsts'] += 1

    # Needs to be A- or above
    if (report.get('grade') is not None) and (report['grade'] >= 4):
      total_report['grade'] += 1

  return total_report

# Total up the number of eligible subdomains.
# Ignore preloaded domains.
def total_https_subdomain_report(eligible):
  total_report = {
    'eligible': 0,
    'uses': 0,
    'enforces': 0,
    'hsts': 0
  }

  for domain in eligible:
    if domain['https']['preloaded'] == 2:
      print("[%s] Skipping subdomain calculation, preloaded." % domain['domain'])
      continue

    subdomains = domain['https'].get('subdomains')
    if subdomains:
      for source in SUBDOMAIN_SOURCES:
        source_data = subdomains.get(source)
        if source_data:
          total_report['eligible'] += source_data['eligible']
          total_report['uses'] += source_data['uses']
          total_report['enforces'] += source_data['enforces']
          total_report['hsts'] += source_data['hsts']

  return total_report


# HTTPS conclusions for a domain based on pshtt/tls domain-scan data.
# Modified subdomain_reports in place.
def https_report_for(domain_name, domain, parent_scan_data, subdomain_reports):
  pshtt = parent_scan_data[domain_name]['pshtt']

  # Initialize to the value of the pshtt report.
  # (Moved to own method to make it reusable for subdomains.)
  report = https_behavior_for(pshtt)

  ###
  # Include the SSL Labs grade for a domain.

  # We may not have gotten any scan data from SSL Labs - it happens.
  tls = parent_scan_data[domain_name].get('tls', None)

  fs = None
  sig = None
  ssl3 = None
  tls12 = None
  rc4 = None

  # Not relevant if no HTTPS
  if (report['uses'] <= 0):
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

  # Initialize subdomain report gatherer if needed.
  agency = domain['agency_slug']
  if subdomain_reports['https'].get(agency) is None:
    subdomain_reports['https'][agency] = []

  # Now load the pshtt data from subdomains, for each source.
  if parent_scan_data[domain_name].get('subdomains'):
    report['subdomains'] = {}
    for source in parent_scan_data[domain_name]['subdomains']:
      print("[%s][%s] Aggregating subdomain data." % (domain_name, source))

      subdomains = parent_scan_data[domain_name]['subdomains'][source]
      eligible = []

      for subdomain in subdomains:
        behavior = https_behavior_for(subdomain)
        eligible.append(behavior)

        # Store the subdomain CSV fields referenced in app/data.py.
        subdomain_reports['https'][agency].append({
          'domain': subdomain['Domain'],
          'base': subdomain['Base Domain'],
          'agency_name': domain['agency_name'],
          'source': source,
          'https': behavior
        })

      subtotals = total_https_report(eligible)
      del subtotals['grade']  # not measured for subdomains
      report['subdomains'][source] = subtotals

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

    # Needs to be present with >= 1 year max-age on canonical endpoint
    if report['hsts'] >= 2:
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

  a11y_domains = Domain.eligible('a11y')
  a11y_report = {'a11y': {}}
  for domain in a11y_domains:
    a11y_report['a11y'][domain['domain']] = domain['a11y']['error_details']

  cust_sat_domains = Domain.eligible('cust_sat')
  total = len(cust_sat_domains)
  participating = 0
  for domain in cust_sat_domains:
    if domain['cust_sat']['participating']:
      participating += 1

  cust_sat_report = {
    'cust_sat': {
      'eligible': total,
      'participating': participating
    }
  }

  return [https_report, analytics_report, a11y_report, cust_sat_report]

# Hacky helper - print out the %'s after the command finishes.
def print_report():
  print()

  report = Report.latest()
  for report_type in report.keys():
    # The a11y report has a very different use than the others
    if report_type == "report_date" or report_type == "a11y":
      continue

    print("[%s]" % report_type)
    eligible = report[report_type]["eligible"]
    for key in report[report_type].keys():
      if key == "eligible":
        continue
      print("%s: %i" % (key, percent(report[report_type][key], eligible)))
    print()

# Convenience: save CSV reports of subdomains per-agency.
def save_subdomain_reports(subdomain_reports):
  # Only works for HTTPS right now.
  for agency in subdomain_reports['https']:
    print("[https][csv][%s] Saving CSV of agency subdomains." % agency)
    output = Domain.subdomains_to_csv(subdomain_reports['https'][agency])
    output_path = os.path.join(ALL_DATA_AGENCIES, agency, "https.csv")
    write(output, output_path)


### utilities

def shell_out(command, env=None):
    try:
        print("[cmd] %s" % str.join(" ", command))
        response = subprocess.check_output(command, shell=False, env=env)
        output = str(response, encoding='UTF-8')
        print(output)
        return output
    except subprocess.CalledProcessError:
        logging.warn("Error running %s." % (str(command)))
        exit(1)
        return None

def percent(num, denom):
  return round((num / denom) * 100)

# mkdir -p in python, from:
# https://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise

def write(content, destination, binary=False):
    mkdir_p(os.path.dirname(destination))

    if binary:
        f = open(destination, 'bw')
    else:
        f = open(destination, 'w', encoding='utf-8')
    f.write(content)
    f.close()


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
    "Government Publishing Office",
    "Congressional Office of Compliance",
    "Stennis Center for Public Service",
    "U.S. Capitol Police",
    "Architect of the Capitol"
  ]:
    return "legislative"

  if agency in [
    "The Judicial Branch (Courts)",
    "The Supreme Court",
    "U.S Courts"
  ]:
    return "judicial"

  if agency in ["Non-Federal Agency"]:
    return "non-federal"

  else:
    return "executive"

### Run when executed.

if __name__ == '__main__':
    run(None, options())
