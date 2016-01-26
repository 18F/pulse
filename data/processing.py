#!/usr/bin/env python

###
#
# Given, in the data/output/scan/results directory:
#
# * domains.csv - federal domains, subset of .gov domain list.
# * inspect.csv - output of domain-scan
# * tls.csv - output of domain-scan
# * analytics.csv - output of domain-scan
#
# Produce, in the data/output/processed directory:
#
#
# = landing pages
# * agencies.json
# * domains.json
#
# = table power
# * tables/https/agencies.json
# * tables/https/domains.json
# * tables/analytics/agencies.json
# * tables/analytics/domains.json
#
# = table data
# * tables/https/domains.csv
# * tables/analytics/domains.csv
#
###

import csv
import json
import os
import slugify


## Input and output dirs, relative to this file.
this_dir = os.path.dirname(__file__)

TABLE_DATA = os.path.join(this_dir, "./output/processed/tables")
STATS_DATA = os.path.join(this_dir, "./output/processed")

INPUT_DOMAINS_DATA = os.path.join(this_dir, "./")
INPUT_SCAN_DATA = os.path.join(this_dir, "./output/scan/results")


LABELS = {
  'https': 'Uses HTTPS',
  'https_forced': 'Enforces HTTPS',
  'hsts': 'Strict Transport Security (HSTS)',
  'hsts_age': 'HSTS max-age',
  'grade': 'SSL Labs Grade',
  'grade_agencies': 'SSL Labs (A- or higher)',
  'dap': 'Participates in DAP?',
  'fs': 'Forward Secrecy',
  'rc4': 'RC4',
  'sig': 'Signature Algorithm',
  'ssl3': 'SSLv3',
  'tls12': 'TLSv1.2',

  # used in export CSVs
  'agency': 'Agency',
  'canonical': 'URL',
  'domain': 'Domain',
  'redirect': 'Redirect',
  'branch': 'Branch'
}

# rows to put in public CSV export
CSV_HTTPS_DOMAINS = [
  'domain', 'branch', 'agency', 'redirect', 'https',  'https_forced', 'hsts', 'grade'
]
CSV_DAP_DOMAINS = [
  'domain', 'branch', 'agency', 'redirect', 'dap'
]



## global data

# big dict of everything in input CSVs
domain_data = {}
agency_data = {}

# lists of uniquely seen domains and agencies, in order
domains = []
agencies = []

# Data as prepared for landing page rendering.
domain_map = {}
agency_map = {}

# Data as prepared for table input.
https_domains = []
analytics_domains = []
https_agencies = []
analytics_agencies = []

###
# Main task flow.

from app import models

def run(date):
  models.clear_database()
  models.Report.create(date)

  # Read in scan CSVs.
  load_data()

  # Calculate high-level conclusions.
  process_domains()

  # Create report percents for each category, save them.
  reports = latest_reports()
  for report in reports:
    models.Report.update(report)

  # Save domains.json and agencies.json for all types.
  save_tables()


# Reads in input CSVs.
def load_data():

  # load in base data from the .gov domain list

  with open(os.path.join(INPUT_DOMAINS_DATA, "domains.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if row[0].lower().startswith("domain"):
        continue

      domain = row[0].lower()
      domain_type = row[1]
      agency = row[2]
      branch = branch_for(agency)

      # Exclude cities, counties, tribes, etc.
      if domain_type != "Federal Agency":
        continue

      # There are a few erroneously marked non-federal domains.
      if branch == "non-federal":
        continue

      if domain not in domains:
        domains.append(domain)
        domain_map[domain] = {
          'domain': domain,
          'branch': branch,
          'agency': agency,
          'agency_slug': slugify.slugify(agency)
        }

      if agency not in agencies:
        agencies.append(agency)

        slug = slugify.slugify(agency)
        agency_map[slug] = {
          'agency': agency,
          'agency_slug': slugify.slugify(agency)
        }

        agency_data[agency] = []

      agency_data[agency].append(domain)

      domain_data[domain] = {
        'branch': branch,
        'agency': agency,
        'agency_slug': slugify.slugify(agency)
      }

  # sort uniquely seen domains and agencies
  domains.sort()
  agencies.sort()

  # store total domains we found
  for agency in agencies:
    slug = slugify.slugify(agency)
    agency_map[slug]['total_domains'] = len(agency_data[agency])

  headers = []
  with open(os.path.join(INPUT_SCAN_DATA, "inspect.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domain_data.get(domain):
        # print("[inspect] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell
      domain_data[domain]['inspect'] = dict_row

  headers = []
  with open(os.path.join(INPUT_SCAN_DATA, "tls.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domain_data.get(domain):
        # print("[tls] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell

      # For now: overwrite previous rows if present, use last endpoint.
      domain_data[domain]['tls'] = dict_row


  # Now, analytics measurement.
  headers = []
  with open(os.path.join(INPUT_SCAN_DATA, "analytics.csv"), newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domain_data.get(domain):
        # print("[analytics] Skipping %s, not a federal domain from domains.csv." % domain)
        continue

      # If it didn't appear in the inspect data, skip it, we need this.
      if not domain_data[domain].get('inspect'):
        # print("[analytics] Skipping %s, did not appear in inspect.csv." % domain)
        continue

      dict_row = {}
      for i, cell in enumerate(row):
        dict_row[headers[i]] = cell

      domain_data[domain]['analytics'] = dict_row

# Given the domain data loaded in from CSVs, draw conclusions,
# and filter/transform data into form needed for display.
def process_domains():

  # First, process all domains.
  for domain in domains:
    if evaluating_for_https(domain):
      row = https_row_for(domain)
      domain_map[domain]['https'] = row
      https_domains.append(row)

    if evaluating_for_analytics(domain):
      row = analytics_row_for(domain)
      domain_map[domain]['analytics'] = row
      analytics_domains.append(row)

  # Second, process each agency's domains.
  for agency in agencies:

    https_total = 0
    https_stats = {
      'https': 0,
      'https_forced': 0,
      'hsts': 0,
      'grade': 0
    }

    analytics_total = 0
    analytics_stats = {
      'dap': 0
    }

    for domain in agency_data[agency]:

      if evaluating_for_https(domain):

        https_total += 1
        row = https_row_for(domain)

        # Needs to be enabled, with issues is allowed
        if row[LABELS['https']] >= 1:
          https_stats['https'] += 1

        # Needs to be Default or Strict to be 'Yes'
        if row[LABELS['https_forced']] >= 2:
          https_stats['https_forced'] += 1

        # Needs to be at least partially present
        if row[LABELS['hsts']] >= 1:
          https_stats['hsts'] += 1

        # Needs to be A- or above
        if row[LABELS['grade']] >= 4:
          https_stats['grade'] += 1

      if evaluating_for_analytics(domain):

        analytics_total += 1
        row = analytics_row_for(domain)

        # Enabled ('Yes')
        if row[LABELS['dap']] >= 1:
          analytics_stats['dap'] += 1


    if https_total > 0:
      row = {
        'Agency': agency,
        'Number of Domains': https_total,
        LABELS['https']: percent(https_stats['https'], https_total),
        LABELS['https_forced']: percent(https_stats['https_forced'], https_total),
        LABELS['hsts']: percent(https_stats['hsts'], https_total),
        LABELS['grade_agencies']: percent(https_stats['grade'], https_total)
      }
      https_agencies.append(row)
      agency_map[slugify.slugify(agency)]['https'] = row
    else:
      agency_map[slugify.slugify(agency)]['https'] = None

    if analytics_total > 0:
      row = {
        'Agency': agency,
        'Number of Domains': analytics_total,
        LABELS['dap']: percent(analytics_stats['dap'], analytics_total)
      }
      analytics_agencies.append(row)
      agency_map[slugify.slugify(agency)]['analytics'] = row
    else:
      agency_map[slugify.slugify(agency)]['analytics'] = None


def evaluating_for_https(domain):
  return (
    (domain_data[domain].get('inspect') is not None) and
    (domain_data[domain]['inspect']["Live"] == "True")
  )

def evaluating_for_analytics(domain):
  return (
    (domain_data[domain].get('inspect') is not None) and
    (domain_data[domain].get('analytics') is not None) and

    (domain_data[domain]['inspect']["Live"] == "True") and
    (domain_data[domain]['inspect']["Redirect"] == "False") and
    (domain_data[domain]['branch'] == "executive")
  )

def https_row_for(domain):
  inspect = domain_data[domain]['inspect']
  row = {
    "Domain": domain,
    "Canonical": inspect["Canonical"],
    "Redirect": boolean_yes(inspect["Redirect"]),
    "Branch": domain_data[domain]['branch'],
    "Agency": domain_data[domain]['agency']
  }

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

  row[LABELS['https']] = https;


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

  row[LABELS['https_forced']] = behavior;


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

  row[LABELS['hsts']] = hsts
  row[LABELS['hsts_age']] = hsts_age


  ###
  # Include the SSL Labs grade for a domain.

  tls = domain_data[domain].get('tls')

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

  row[LABELS['grade']] = grade
  row[LABELS['fs']] = fs
  row[LABELS['sig']] = sig
  row[LABELS['rc4']] = rc4
  row[LABELS['ssl3']] = ssl3
  row[LABELS['tls12']] = tls12

  return row

# Given the data we have about a domain, what's the DAP row?
def analytics_row_for(domain):
  analytics = domain_data[domain]['analytics']
  inspect = domain_data[domain]['inspect']

  row = {
    "Domain": domain,
    "Canonical": inspect["Canonical"],
    "Redirect": boolean_yes(inspect["Redirect"]),
    "Branch": domain_data[domain]['branch'],
    "Agency": domain_data[domain]['agency']
  }

  # rename column in process
  row[LABELS['dap']] = boolean_nice(analytics['Participates in Analytics'])

  return row

# Make a tiny CSV about each stat, to be downloaded for D3 rendering.
def latest_reports():

  total = len(https_domains)
  enabled = 0
  enforced = 0
  hsts = 0
  for row in https_domains:
    # HTTPS needs to be enabled.
    # It's okay if it has a bad chain.
    # However, it's not okay if HTTPS is downgraded.
    if (
      (row[LABELS['https']] >= 1) and
      (row[LABELS['https_forced']] >= 1)
    ):
      enabled += 1

    # Needs to be Default or Strict to be 'Yes'
    if row[LABELS['https_forced']] >= 2:
      enforced += 1

    # Needs to be at least partially present
    if row[LABELS['hsts']] >= 1:
      hsts += 1

  print("Uses HTTPS: %i%%" % percent(enabled, total))
  print("Enforces HTTPS: %i%%" % percent(enforced, total))
  print("Uses HSTS: %i%%" % percent(hsts, total))

  https_report = {
    'https': {
      'eligible': total,
      'uses': percent(enabled, total),
      'enforces': percent(enforced, total),
      'hsts': percent(hsts, total)
    }
  }

  total = len(analytics_domains)
  enabled = 0
  for row in analytics_domains:
    # Enabled ('Yes')
    if row[LABELS['dap']] >= 1:
      enabled += 1


  analytics_report = {
    'analytics': {
      'eligible': total,
      'participating': percent(enabled, total)
    }
  }

  return [https_report, analytics_report]

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

# Given the rows we've made, save them to disk.
def save_tables():
  https_path = os.path.join(TABLE_DATA, "https/domains.json")
  https_data = json_for({'data': https_domains})
  write(https_data, https_path)


  header_row = []
  for label in CSV_HTTPS_DOMAINS:
    header_row.append(LABELS[label])
  csv_https_rows = [header_row]
  for domain in https_domains:
    row = []
    for label in CSV_HTTPS_DOMAINS:
      cell = str(domain[LABELS[label]])

      # If we have a display mapping of e.g. 1 -> "Yes", run it.
      # This is synced manually with the JS mapping, which is bad.
      if CSV_HTTPS_MAPPING.get(label):
        cell = CSV_HTTPS_MAPPING[label][cell]

      row.append(cell)
    csv_https_rows.append(row)
  save_csv(csv_https_rows, TABLE_DATA, "https/https-domains.csv")

  header_row = []
  for label in CSV_DAP_DOMAINS:
    header_row.append(LABELS[label])
  csv_dap_rows = [header_row]
  for domain in analytics_domains:
    row = []
    for label in CSV_DAP_DOMAINS:
      cell = str(domain[LABELS[label]])

      # If we have a display mapping of e.g. 1 -> "Yes", run it.
      # This is synced manually with the JS mapping, which is bad.
      if CSV_DAP_MAPPING.get(label):
        cell = CSV_DAP_MAPPING[label][cell]

      row.append(cell)

    csv_dap_rows.append(row)
  save_csv(csv_dap_rows, TABLE_DATA, "analytics/analytics-domains.csv")

  https_agencies_path = os.path.join(TABLE_DATA, "https/agencies.json")
  https_agencies_data = json_for({'data': https_agencies})
  write(https_agencies_data, https_agencies_path)

  analytics_path = os.path.join(TABLE_DATA, "analytics/domains.json")
  analytics_data = json_for({'data': analytics_domains})
  write(analytics_data, analytics_path)

  analytics_agencies_path = os.path.join(TABLE_DATA, "analytics/agencies.json")
  analytics_agencies_data = json_for({'data': analytics_agencies})
  write(analytics_agencies_data, analytics_agencies_path)

def save_csv(rows, directory, filename):
  full_output = os.path.join(directory, filename)
  os.makedirs(os.path.dirname(full_output), exist_ok=True)
  f = open(os.path.join(directory, filename), 'w', newline='')
  writer = csv.writer(f)
  for row in rows:
    writer.writerow(row)
  f.close()


### utilities

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


### Stupid mapping sync.

"""
I don't like this at all, but to keep the presentation synced
between the front-end table, and the CSV we generate, this is
getting replicated to the JavaScript files in this repository,
and needs to be manually synced.

The refactor that takes away from DataTables should also prioritize
a cleaner way to DRY ("don't repeat yourself") this mess up.
"""
CSV_HTTPS_MAPPING = {

  'https': {
    "-1": "No",
    '0': "No",
    '1': "Yes", # (with certificate chain issues)
    '2': "Yes"
  },

  'https_forced': {
    '0': "", # N/A (no HTTPS)
    '1': "No", # Present, not default
    '2': "Yes", # Defaults eventually to HTTPS
    '3': "Yes" # Defaults eventually + redirects immediately
  },

  'hsts': {
    "-1": "", # N/A
    '0': "No", # No
    '1': "Yes", # HSTS on only that domain
    '2': "Yes", # HSTS on subdomains
    '3': "Yes, and preload-ready", # HSTS on subdomains + preload flag
    '4': "Yes, and preloaded" # In the HSTS preload list
  },

  'grade': {
    "-1": "",
    '0': "F",
    '1': "T",
    '2': "C",
    '3': "B",
    '4': "A-",
    '5': "A",
    '6': "A+"
  }
}

CSV_DAP_MAPPING = {
  'dap': {
    '0': "No",
    '1': "Yes"
  }
}

### Run when executed.

if __name__ == '__main__':
    run()
