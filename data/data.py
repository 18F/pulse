#!/usr/bin/env python

###
#
# Given, in the data/ directory:
#
# * domains.csv - federal domains, subset of .gov domain list.
# * inspect.csv - output of domain-scan
# * analytics.csv - output of domain-scan
#
# Produce, in the assets/data/ directory:
#
# * https.json - JSON version of HTTPS stats.
# * analytics.json - JSON version of DAP stats.
# * stats.json - aggregate numbers for DAP, HTTPS, and a timestamp.
#
###

import csv
import json
import os

## Output dirs.

TABLE_DATA = "../assets/data/tables"
STATS_DATA = "../assets/data"


## global data

# big dict of everything in input CSVs
domain_data = {}
agency_data = {}

# lists of uniquely seen domains and agencies, in order
domains = []
agencies = []

# Data as prepared for table input.
https_domains = []
analytics_domains = []
https_agencies = []
analytics_agencies = []

# Stats data as prepared for direct rendering.
https_stats = []
analytics_stats = []

###
# Main task flow.

def run():
  load_data()
  process_domains()
  process_stats()
  save_tables()
  save_stats()


# Reads in input CSVs.
def load_data():

  # load in base data from the .gov domain list

  with open("domains.csv", newline='') as csvfile:
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

      if agency not in agencies:
        agencies.append(agency)
        agency_data[agency] = []

      agency_data[agency].append(domain)

      domain_data[domain] = {
        'branch': branch,
        'agency': agency
      }

  # sort uniquely seen domains and agencies
  domains.sort()
  agencies.sort()

  headers = []
  with open("inspect.csv", newline='') as csvfile:
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


  # Now, analytics measurement.
  headers = []
  with open("analytics.csv", newline='') as csvfile:
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

# Given the domain data loaded in from CSVs, initialize the
# main domains arrays with filtered data.
def process_domains():

  for domain in domains:
    if evaluating_for_https(domain):
      https_domains.append(https_row_for(domain))

    if evaluating_for_analytics(domain):
      analytics_domains.append(analytics_row_for(domain))


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

'''
Given the data we have about a domain, what's the HTTPS row?

{
  "Domain": [domain],
  "HTTPS Enabled?": [
    "No" | "Yes (with issues)" | "Yes"
  ],
  "HTTPS Enforced?": [
    "No" | "Yes" | "Yes (Strict)"
  ],
  "HSTS": [
    "No" | "Yes (Partial)" | "Yes (Complete)"
  ]
}
'''
def https_row_for(domain):
  inspect = domain_data[domain]['inspect']
  row = {"Domain": domain}

  ###
  # Is it there? There for most clients? Not there?

  if (inspect["Valid HTTPS"] == "True"):
    https = "Yes"
  elif (inspect["HTTPS Bad Chain"] == "True"):
    https = "Yes (with issues)"
  else:
    https = "No"

  row["HTTPS Enabled?"] = https;


  ###
  # Characterize the HTTPS setup on the domain.

  # It's a "No" if HTTPS isn't present.
  if (https == "No"):
    behavior = "No"

  else:
    # It's a "No" if HTTPS redirects down to HTTP.
    if (inspect["Downgrades HTTPS"] == "True"):
      behavior = "No"

    # "Yes (Strict)" means HTTP immediately redirects to HTTPS,
    # *and* that HTTP eventually redirects to HTTPS.
    elif (
      (inspect["Strictly Forces HTTPS"] == "True") and
      (inspect["Defaults to HTTPS"] == "True")
    ):
      behavior = "Yes (Strict)"

    # "Yes" means HTTP eventually redirects to HTTPS.
    elif (
      (inspect["Strictly Forces HTTPS"] == "False") and
      (inspect["Defaults to HTTPS"] == "True")
    ):
      behavior = "Yes";

    # Either both are False, or just 'Strict Force' is True,
    # which doesn't matter on its own.
    else:
      behavior = "No";

  row["HTTPS Enforced?"] = behavior;


  ###
  # Characterize the presence and completeness of HSTS.

  # Without HTTPS there can be no HSTS.
  if (https == "No"):
    hsts = "No"

  else:

    # HTTPS is there, but no HSTS header.
    if (inspect["HSTS"] == "False"):
      hsts = "No"

    # "Complete" means HSTS preload ready (long max-age).
    elif (inspect["HSTS Preload Ready"] == "True"):
      hsts = "Yes (Complete)"

    # This kind of "Partial" means `includeSubdomains`, but no `preload`.
    elif (inspect["HSTS All Subdomains"] == "True"):
      hsts = "Yes (Partial)"

    # This kind of "Partial" means HSTS, but not on subdomains.
    else: # if (inspect["HSTS"] == "True"):
      hsts = "Yes (Partial)"

  row["Strict Transport Security (HSTS)"] = hsts;

  return row

# Given the data we have about a domain, what's the DAP row?
def analytics_row_for(domain):
  row = dict.copy(domain_data[domain]['analytics'])

  # TODO: maybe there's a better way to rename this column?
  row['Participates in DAP?'] = row['Participates in Analytics']
  del row["Participates in Analytics"]

  return row

# Make a tiny CSV about each stat, to be downloaded for D3 rendering.
def process_stats():
  global https_stats, analytics_stats

  total = len(https_domains)
  enabled = 0
  for row in https_domains:
    if row['HTTPS Enabled?'] != "No":
      enabled += 1
  pct = percent(enabled, total)

  https_stats = [
    ['status', 'value'],
    ['active', pct],
    ['inactive', 100-pct]
  ]

  total = len(analytics_domains)
  enabled = 0
  for row in analytics_domains:
    if row['Participates in DAP?'] == "True":
      enabled += 1
  pct = percent(enabled, total)

  analytics_stats = [
    ['status', 'value'],
    ['active', pct],
    ['inactive', 100-pct]
  ]


def percent(num, denom):
  return round((num / denom) * 100)

# Given the rows we've made, save them to disk.
def save_tables():
  https_path = os.path.join(TABLE_DATA, "https/domains.json")
  https_data = json_for({'data': https_domains})
  write(https_data, https_path)

  analytics_path = os.path.join(TABLE_DATA, "analytics/domains.json")
  analytics_data = json_for({'data': analytics_domains})
  write(analytics_data, analytics_path)

# Given the rows we've made, save some top-level #'s to disk.
def save_stats():
  f = open(os.path.join(STATS_DATA, "https.csv"), 'w', newline='')
  writer = csv.writer(f)
  for row in https_stats:
    writer.writerow(row)
  f.close()

  f = open(os.path.join(STATS_DATA, "analytics.csv"), 'w', newline='')
  writer = csv.writer(f)
  for row in analytics_stats:
    writer.writerow(row)
  f.close()



### utilities

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
    run()
