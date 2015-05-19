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

domains = {}
https = []
analytics = []

def run():
  global domains, https, analytics

  load_data()
  save_tables()
  save_stats()



# Reads in input CSVs.
def load_data():

  # load in base data from the .gov domain list

  with open("domains.csv", newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (not row[0]) or (row[0].lower().startswith("domain")):
        continue

      domain = row[0].lower()
      # row[1] is just "Federal Agency"
      # TODO: take in the official full list, but filter out others
      branch = branch_for(row[2])

      if branch == "non-federal":
        continue

      domains[domain] = {
        'branch': branch
      }

  headers = []
  with open("inspect.csv", newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domains.get(domain):
        continue

      json_row = {}
      for i, cell in enumerate(row):
        json_row[headers[i]] = cell
      json_row['Branch'] = domains[domain]['branch']

      https.append(json_row)
      domains[domain]['https'] = json_row

  # Now, analytics measurement.
  headers = []
  with open("analytics.csv", newline='') as csvfile:
    for row in csv.reader(csvfile):
      if (row[0].lower() == "domain"):
        headers = row
        continue

      domain = row[0].lower()
      if not domains.get(domain):
        continue

      # If it didn't appear in the inspect data, skip it, we need this.
      if not domains[domain].get('https'):
        continue

      json_row = {}
      for i, cell in enumerate(row):
        json_row[headers[i]] = cell

      json_row['Redirect'] = domains[domain]['https']['Redirect']
      json_row['Live'] = domains[domain]['https']['Live']
      json_row['Branch'] = domains[domain]['branch']

      analytics.append(json_row)
      domains[domain]['analytics'] = json_row

def save_tables():
  https_path = os.path.join(TABLE_DATA, "https-domains.json")
  https_data = json_for({'data': https})
  write(https_data, https_path)

  analytics_path = os.path.join(TABLE_DATA, "analytics-domains.json")
  analytics_data = json_for({'data': analytics})
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
