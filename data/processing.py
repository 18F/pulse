###
#
# Given, in the data/output/parents/results directory:
#
# * pshtt.csv - domain-scan, based on pshtt
# * sslyze.csv - domain-scan, based on sslyze.
# * analytics.csv - domain-scan, based on analytics.usa.gov data
# * a11y.csv (optional) - pa11y scan data
# * third_parties.csv (optional) - third party scan data
#
# And, in the data/output/subdomains directory:
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
SUBDOMAIN_DATA_AGENCIES = os.path.join(SUBDOMAIN_DATA, "./agencies")
SUBDOMAIN_DOMAINS_CSV = os.path.join(SUBDOMAIN_DATA_GATHERED, "results", "gathered.csv")

A11Y_ERRORS = {
  '1_1': 'Missing Image Descriptions',
  '1_3': 'Form - Initial Findings',
  '1_4': 'Color Contrast - Initial Findings',
  '4_1': 'HTML Attribute - Initial Findings',
  None: 'Other Errors'
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

  # Calculate high-level per-domain conclusions for each report.
  # Overwrites `domains` and `subdomains` in-place.
  process_domains(domains, agencies, subdomains, parent_scan_data, subdomain_scan_data)

  # Reset the database.
  print("Clearing the database.")
  models.clear_database()

  # Calculate agency-level summaries. Updates `agencies` in-place.
  update_agency_totals(agencies, domains, subdomains)

  # Calculate government-wide summaries.
  report = full_report(domains, subdomains)
  report['report_date'] = date

  print("Creating all domains.")
  Domain.create_all(domains[domain_name] for domain_name in sorted_domains)
  print("Creating all subdomains.")
  Domain.create_all(subdomains[subdomain_name] for subdomain_name in sorted_subdomains)
  print("Creating all agencies.")
  Agency.create_all(agencies[agency_name] for agency_name in sorted_agencies)

  # Create top-level summaries.
  print("Creating government-wide totals.")
  Report.create(report)

  # Print and exit
  print_report(report)


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

      # Exclude non-federal branches. (Sigh.)
      if branch != "executive":
        continue

      if domain_name not in domain_map:
        domain_map[domain_name] = {
          'domain': domain_name,
          'base_domain': domain_name,
          'agency_name': agency_name,
          'agency_slug': agency_slug,
          'sources': ['dotgov'],
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

  with open(SUBDOMAIN_DOMAINS_CSV, newline='') as csvfile:
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
        # print("[pshtt] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell
      parent_scan_data[domain]['pshtt'] = dict_row

  headers = []
  with open(os.path.join(PARENT_RESULTS, "sslyze.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domains.get(domain):
        # print("[sslyze] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell
      parent_scan_data[domain]['sslyze'] = dict_row

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
  pshtt_subdomains_csv = os.path.join(SUBDOMAIN_DATA_SCANNED, "results", "pshtt.csv")

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
          'base_domain': parent_domain,
          'agency_slug': domains[parent_domain]['agency_slug'],
          'agency_name': domains[parent_domain]['agency_name'],
          'branch': domains[parent_domain]['branch'],
          'is_parent': False,
          'sources': gathered_subdomains[subdomain]
        }

  # Load in sslyze subdomain data.
  # Note: if we ever add more subdomain scanners, this loop
  # could be genericized and iterated over really easily.
  sslyze_subdomains_csv = os.path.join(SUBDOMAIN_DATA_SCANNED, "results", "sslyze.csv")

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

  # For each domain, determine eligibility and, if eligible,
  # use the scan data to draw conclusions.
  for domain_name in domains.keys():

    ### HTTPS
    #
    # For HTTPS, we calculate individual reports for every subdomain.

    https_parent = {
      'eligible': False, # domain eligible itself (is it live?)
      'eligible_zone': False, # zone eligible (itself or any live subdomains?)
    }
    eligible_children = []
    eligible_zone = False

    # No matter what, put the preloaded state onto the parent,
    # since even an unused domain can always be preloaded.
    https_parent['preloaded'] = preloaded_or_not(
      parent_scan_data[domain_name]['pshtt']
    )

    # Tally subdomains first, so we know if the parent zone is
    # definitely eligible as a zone even if not as a website
    for subdomain_name in parent_scan_data[domain_name].get('subdomains', []):

      if eligible_for_https(subdomains[subdomain_name]):
        eligible_children.append(subdomain_name)
        subdomains[subdomain_name]['https'] = https_behavior_for(
          subdomain_name,
          subdomain_scan_data[subdomain_name]['pshtt'],
          subdomain_scan_data[subdomain_name].get('sslyze', None),
          parent_preloaded=https_parent['preloaded']
        )

    # ** syntax merges dicts, available in 3.5+
    if eligible_for_https(domains[domain_name]):
      https_parent = {**https_parent, **https_behavior_for(
        domain_name,
        parent_scan_data[domain_name]['pshtt'],
        parent_scan_data[domain_name].get('sslyze', None)
      )}
      https_parent['eligible_zone'] = True

    # even if not eligible directly, can be eligible via subdomains
    elif len(eligible_children) > 0:
        https_parent['eligible_zone'] = True

    # If the parent zone is preloaded, make sure that each subdomain
    # is considered to have HSTS in place. If HSTS is yes on its own,
    # leave it, but if not, then grant it the minimum level.
    # TODO:

    domains[domain_name]['https'] = https_parent

    # Totals based on summing up eligible reports within this domain.
    totals = {}

    # For HTTPS/HSTS, pshtt-eligible parent + subdomains.
    eligible_reports = [subdomains[name]['https'] for name in eligible_children]
    if https_parent['eligible']:
      eligible_reports = [https_parent] + eligible_reports
    totals['https'] = total_https_report(eligible_reports)

    # For SSLv2/SSLv3/RC4/3DES, sslyze-eligible parent + subdomains.
    subdomain_names = parent_scan_data[domain_name].get('subdomains', [])
    eligible_reports = [subdomains[name]['https'] for name in subdomain_names if subdomains[subdomain_name].get('https') and subdomains[subdomain_name]['https'].get('rc4') is not None]
    if https_parent and https_parent.get('rc4') is not None:
      eligible_reports = [https_parent] + eligible_reports
    totals['crypto'] = total_crypto_report(eligible_reports)

    domains[domain_name]['totals'] = totals

    ### Everything else
    #
    # For other reports, we still focus only on parent domains.
    if eligible_for_analytics(domains[domain_name]):
      domains[domain_name]['analytics'] = analytics_report_for(
        domain_name, domains[domain_name], parent_scan_data
      )

    if eligible_for_a11y(domains[domain_name]):
      domains[domain_name]['a11y'] = a11y_report_for(
        domain_name, domains[domain_name], parent_scan_data
      )

    if eligible_for_cust_sat(domains[domain_name]):
      domains[domain_name]['cust_sat'] = cust_sat_report_for(
        domain_name, domains[domain_name], parent_scan_data
      )

# Given a list of domains or subdomains, quick filter to which
# are eligible for this report, optionally for an agency.
def eligible_for(report, hosts, agency=None):
  return [host[report] for hostname, host in hosts.items() if (host.get(report) and host[report]['eligible'] and ((agency is None) or (host['agency_slug'] == agency['slug'])))]

# Go through each report type and add agency totals for each type.
def update_agency_totals(agencies, domains, subdomains):

  # For each agency, update their report counts for every domain they have.
  for agency_slug in agencies.keys():
    agency = agencies[agency_slug]

    # HTTPS. Parent and subdomains.
    # print("[%s][%s] Totalling report." % (agency['slug'], 'https'))
    eligible = eligible_for('https', domains, agency) + eligible_for('https', subdomains, agency)
    agency['https'] = total_https_report(eligible)

    # Separate report for crypto, for sslyze-scanned domains.
    # print("[%s][%s] Totalling report." % (agency['slug'], 'crypto'))
    eligible = [domain['https'] for name, domain in domains.items() if (domain['agency_slug'] == agency['slug']) and domain.get('https') and (domain['https'].get('rc4') is not None)]
    eligible = eligible + [subdomain['https'] for name, subdomain in subdomains.items() if (subdomain['agency_slug'] == agency['slug']) and subdomain.get('https') and (subdomain['https'].get('rc4') is not None)]
    agency['crypto'] = total_crypto_report(eligible)

    # Special separate report for preloaded parent domains.
    # All parent domains, whether they use HTTP or not, are eligible.
    # print("[%s][%s] Totalling report." % (agency['slug'], 'preloading'))
    eligible = [host['https'] for hostname, host in domains.items() if host['agency_slug'] == agency_slug]
    agency['preloading'] = total_preloading_report(eligible)


    # Analytics. Parent domains.
    # print("[%s][%s] Totalling report." % (agency['slug'], 'analytics'))
    eligible = eligible_for('analytics', domains, agency)
    totals = {
      'eligible': len(eligible),
      'participating': 0
    }
    for report in eligible:
      if report['participating'] == True:
        totals['participating'] += 1
    agency['analytics'] = totals


    # Accessibility. Parent domains.
    # print("[%s][%s] Totalling report." % (agency['slug'], 'a11y'))
    eligible = eligible_for('a11y', domains, agency)
    pages_count = len(eligible)
    errors = {e:0 for e in A11Y_ERRORS.values()}
    for a11y in eligible:
      for error in a11y['errorlist']:
        errors[error] += a11y['errorlist'][error]
    total_errors = sum(errors.values())
    avg_errors_per_page = (
      'n/a' if pages_count == 0 else round(float(total_errors) / pages_count, 2)
    )
    totals = {
      'eligible': pages_count,
      'pages_count': pages_count,
      'Average Errors per Page': avg_errors_per_page
    }
    if pages_count:
      averages = ({
        e: round(mean([report['errorlist'][e] for report in eligible]), 2)
        for e in A11Y_ERRORS.values()
      })
    else:
      averages = {e: 'n/a' for e in A11Y_ERRORS.values()}
    totals.update(averages)
    agency['a11y'] = totals


    # Customer satisfaction. Parent domains.
    # print("[%s][%s] Totalling report." % (agency['slug'], 'cust_sat'))
    eligible = eligible_for('cust_sat', domains, agency)
    agency['cust_sat'] = {
      'eligible': len(eligible),
      'participating': len([report for report in eligible if report['participating']])
    }

# Create a Report about each tracked stat.
def full_report(domains, subdomains):

  full = {}

  # HTTPS. Parent and subdomains.
  print("[https] Totalling full report.")
  eligible = eligible_for('https', domains) + eligible_for('https', subdomains)
  full['https'] = total_https_report(eligible)

  print("[crypto] Totalling full report.")
  eligible = [domain['https'] for name, domain in domains.items() if domain.get('https') and (domain['https'].get('rc4') is not None)]
  eligible = eligible + [subdomain['https'] for name, subdomain in subdomains.items() if subdomain.get('https') and (subdomain['https'].get('rc4') is not None)]
  full['crypto'] = total_crypto_report(eligible)

  # Special separate report for preloaded parent domains.
  # All parent domains, whether they use HTTP or not, are eligible.
  print("[preloading] Totalling full report.")
  eligible = [host['https'] for hostname, host in domains.items()]
  full['preloading'] = total_preloading_report(eligible)

  # Analytics. Parent domains only.
  print("[analytics] Totalling full report.")
  eligible = eligible_for('analytics', domains)
  participating = 0
  for report in eligible:
    if report['participating'] == True:
      participating += 1
  full['analytics'] = {
    'eligible': len(eligible),
    'participating': participating
  }


  # a11y report. Parent domains.
  # Constructed very differently.
  print("[a11y] Totalling full report.")
  eligible_domains = [host for hostname, host in domains.items() if (host.get('a11y') and host['a11y']['eligible'])]
  full['a11y'] = {}
  for domain in eligible_domains:
    full['a11y'][domain['domain']] = domain['a11y']['error_details']


  # Customer satisfaction report. Parent domains.
  print("[cust_sat] Totalling full report.")
  eligible = eligible_for('cust_sat', domains)

  participating = 0
  for report in eligible:
    if report['participating']:
      participating += 1
  full['cust_sat'] = {
    'eligible': len(eligible),
    'participating': participating
  }

  return full


def eligible_for_https(domain):
  return (
    (domain["live"] == True) and
    (domain["branch"] == "executive")
  )

def eligible_for_analytics(domain):
  return (
    (domain["live"] == True) and
    (domain["redirect"] == False) and
    (domain["branch"] == "executive") and
    # managed in data/ineligible/analytics.yml
    (
      (domain.get("exclude") is None) or
      (domain["exclude"].get("analytics") is None) or
      (domain["exclude"]["analytics"] == False)
    )
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
  if parent_scan_data[domain_name].get('analytics') is None:
    return None

  analytics = parent_scan_data[domain_name]['analytics']
  pshtt = parent_scan_data[domain_name]['pshtt']

  return {
    'eligible': True,
    'participating': boolean_for(analytics['Participates in Analytics'])
  }

def a11y_report_for(domain_name, domain, parent_scan_data):
  if parent_scan_data[domain_name].get('a11y') is None:
    return None

  a11y_report = {
    'eligible': True,
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
  if parent_scan_data[domain_name].get('cust_sat') is None:
    return None

  cust_sat_report = {
    'eligible': True,
    'service_list': {},
    'participating': False
  }
  if parent_scan_data[domain_name].get('cust_sat'):
    cust_sat = parent_scan_data[domain_name]['cust_sat']
    externals = [d.strip() for d in cust_sat['All External Domains'].split(',')]
    cust_sat_tools = [CUSTOMER_SATISFACTION_TOOLS[x] for
                      x in externals if
                      x in CUSTOMER_SATISFACTION_TOOLS]
    cust_sat_report['service_list'] = {s:CUSTOMER_SATISFACTION_URLS[s] for
                                     s in cust_sat_tools}
    cust_sat_report['participating'] = len(cust_sat_tools) > 0

  return cust_sat_report

# Given a pshtt report and (optional) sslyze report,
# fill in a dict with the conclusions.
def https_behavior_for(name, pshtt, sslyze, parent_preloaded=None):
  report = {
    'eligible': True
  }

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

  # If this is a subdomain, it can be considered as having HSTS, via
  # the preloading of its parent.
  if parent_preloaded:
    hsts = 3 # Yes, via preloading

  # Otherwise, without HTTPS there can be no HSTS for the domain directly.
  elif (https <= 0):
    hsts = -1  # N/A (considered 'No')

  else:

    # HSTS is present for the canonical endpoint.
    if (pshtt["HSTS"] == "True") and hsts_age:

      # Say No for too-short max-age's, and note in the extended details.
      if hsts_age >= 31536000:
        hsts = 2  # Yes, directly
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

  ###
  # Get cipher/protocol data via sslyze for a host.

  sslv2 = None
  sslv3 = None
  any_rc4 = None
  any_3des = None

  # values: unknown or N/A (-1), No (0), Yes (1)
  bod_crypto = None

  # N/A if no HTTPS
  if (report['uses'] <= 0):
    bod_crypto = -1 # N/A

  elif sslyze is None:
    # print("[https][%s] No sslyze scan data found." % name)
    bod_crypto = -1 # Unknown

  else:
    ###
    # BOD 18-01 (cyber.dhs.gov) cares about SSLv2, SSLv3, RC4, and 3DES.
    any_rc4 = boolean_for(sslyze["Any RC4"])
    # TODO: kill conditional once everything is synced
    if sslyze.get("Any 3DES"):
      any_3des = boolean_for(sslyze["Any 3DES"])
    sslv2 = boolean_for(sslyze["SSLv2"])
    sslv3 = boolean_for(sslyze["SSLv3"])

    if any_rc4 or any_3des or sslv2 or sslv3:
      bod_crypto = 0
    else:
      bod_crypto = 1

  report['bod_crypto'] = bod_crypto
  report['rc4'] = any_rc4
  report['3des'] = any_3des
  report['sslv2'] = sslv2
  report['sslv3'] = sslv3

  # Final calculation: is the service compliant with all of M-15-13
  # (HTTPS+HSTS) and BOD 18-01 (that + RC4/3DES/SSLv2/SSLv3)?

  # For M-15-13 compliance, the service has to enforce HTTPS,
  # and has to have strong HSTS in place (can be via preloading).
  m1513 = (behavior >= 2) and (hsts >= 2)

  # For BOD compliance, only ding if we have scan data:
  # * If our scanner dropped, give benefit of the doubt.
  # * If they have no HTTPS, this will fix itself once HTTPS comes on.
  bod1801 = m1513 and (bod_crypto != 0)

  # Phew!
  report['m1513'] = m1513
  report['compliant'] = bod1801 # equivalent, since BOD is a superset

  return report

# Just returns a 0 or 2 for inactive (not live) zones, where
# we still may care about preloaded state.
def preloaded_or_not(pshtt):
  if pshtt["HSTS Preloaded"] == "True":
    return 2  # Yes
  else:
    return 0 # No

# 'eligible' should be a list of dicts with https report data.
def total_https_report(eligible):
  total_report = {
    'eligible': len(eligible),
    'uses': 0,
    'enforces': 0,
    'hsts': 0,

    # compliance roll-ups
    'm1513': 0,
    'compliant': 0
  }

  for report in eligible:

    # Needs to be enabled, with issues is allowed
    if report['uses'] >= 1:
      total_report['uses'] += 1

    # Needs to be Default or Strict to be 'Yes'
    if report['enforces'] >= 2:
      total_report['enforces'] += 1

    # Needs to be present with >= 1 year max-age for canonical endpoint,
    # or preloaded via its parent zone.
    if report['hsts'] >= 2:
      total_report['hsts'] += 1

    # Factors in crypto score, but treats ineligible services as passing.
    for field in ['m1513', 'compliant']:
      if report[field]:
        total_report[field] += 1

  return total_report

def total_crypto_report(eligible):
  total_report = {
    'eligible': len(eligible),
    'bod_crypto': 0,
    'rc4': 0,
    '3des': 0,
    'sslv2': 0,
    'sslv3': 0
  }

  for report in eligible:
    if report.get('bod_crypto') is None:
      continue

    # Needs to be a Yes
    if report['bod_crypto'] == 1:
      total_report['bod_crypto'] += 1

    # Tracking separately, may not display separately
    if report['rc4']:
      total_report['rc4'] += 1
    if report['3des']:
      total_report['3des'] += 1
    if report['sslv2']:
      total_report['sslv2'] += 1
    if report['sslv3']:
      total_report['sslv3'] += 1

  return total_report

def total_preloading_report(eligible):
  total_report = {
    'eligible': len(eligible),
    'preloaded': 0,
    'preload_ready': 0
  }

  # Tally preloaded and preload-ready
  for report in eligible:
    # We consider *every* domain eligible for preloading,
    # so there may be no pshtt data for some.
    if report.get('preloaded') is None:
      continue

    if report['preloaded'] == 1:
      total_report['preload_ready'] += 1
    elif report['preloaded'] == 2:
      total_report['preloaded'] += 1

  return total_report

# Hacky helper - print out the %'s after the command finishes.
def print_report(report):
  print()

  for report_type in report.keys():
    # The a11y report has a very different use than the others
    if report_type == "report_date" or report_type == "a11y":
      continue

    print("[%s]" % report_type)
    eligible = report[report_type]["eligible"]
    for key in report[report_type].keys():
      if key == "eligible":
        print("%s: %i" % (key, report[report_type][key]))
      else:
        print("%s: %i%% (%i)" % (key, percent(report[report_type][key], eligible), report[report_type][key]))
    print()


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
  if denom == 0: return 0 # for shame!
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
