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
STATS_DATA = "../_data"


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
stats = {}

def run():
  load_data()
  # print(json_for(agency_data))
  filter_domains()
  # group_domains()
  # group_agencies()
  save_tables()
  # save_stats()


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
def filter_domains():

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

def https_row_for(domain):
  return dict.copy(domain_data[domain]['inspect'])

def analytics_row_for(domain):
  row = dict.copy(domain_data[domain]['analytics'])
  row['Redirect'] = domain_data[domain]['inspect']['Redirect']
  row['Live'] = domain_data[domain]['inspect']['Live']
  row['Branch'] = domain_data[domain]['branch']
  return row

def save_tables():
  https_path = os.path.join(TABLE_DATA, "https-domains.json")
  https_data = json_for({'data': https_domains})
  write(https_data, https_path)

  analytics_path = os.path.join(TABLE_DATA, "analytics-domains.json")
  analytics_data = json_for({'data': analytics_domains})
  write(analytics_data, analytics_path)

def save_stats():
  pass


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
