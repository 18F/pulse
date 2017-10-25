##
# This file must be run as a module in order for it to access
# modules in sibling directories.
#
# Run with:
#   python -m data.update

import subprocess
import datetime
import os
import sys
import yaml
import ujson
import logging

import data.processing

# Orchestrate the overall regular Pulse update process.
#
# Steps:
#
# 1. Kick off domain-scan to scan each domain for each measured thing.
#    - Should drop results into data/output/parents (or a symlink).
#    - If exits with non-0 code, this should exit with non-0 code.
#
# 1a. Subdomains.
#    - Gather latest subdomains from public sources, into one condensed deduped file.
#    - Run pshtt and sslyze on gathered subdomains.
#    - This creates 2 resulting CSVs: pshtt.csv and sslyze.csv
#
# 2. Run processing.py to generate front-end-ready data as data/db.json.
#
# 3. Upload data to S3.
#    - Depends on the AWS CLI and access credentials already being configured.
#    - TODO: Consider moving from aws CLI to Python library.

this_dir = os.path.dirname(__file__)

# App-level metadata.
META = yaml.safe_load(open(os.path.join(this_dir, "../meta.yml")))
DOMAINS = os.environ.get("DOMAINS", META["data"]["domains_url"])

# domain-scan paths (MUST be set in env)
SCAN_COMMAND = os.environ.get("DOMAIN_SCAN_PATH", None)
GATHER_COMMAND = os.environ.get("DOMAIN_GATHER_PATH", None)


# post-processing and uploading information
PARENTS_DATA = os.path.join(this_dir, "./output/parents")
ALL_DATA = os.path.join(this_dir, "./output/all")
ALL_DATA_GATHERED = os.path.join(this_dir, "./output/all/gather")
ALL_DATA_SCANNED = os.path.join(this_dir, "./output/all/scan")

DB_DATA = os.path.join(this_dir, "./db.json")
BUCKET_NAME = META['bucket']

# DAP source data
ANALYTICS_URL = META["data"]["analytics_url"]

# a11y source data
A11Y_CONFIG = META["a11y"]["config"]
A11Y_REDIRECTS = META["a11y"]["redirects"]

### Parent domain scanning information
#
SCANNERS = os.environ.get("SCANNERS", "pshtt,analytics,a11y,third_parties")

### subdomain gathering/scanning information
GATHER_SUFFIX = ".gov"

# names and options must be in corresponding order
GATHERER_NAMES = ["censys", "dap", "eot2016", "parents"]
GATHERER_OPTIONS = [
  "--export",
  "--dap=%s" % META["data"]["analytics_subdomains_url"],
  "--eot2016=%s" % META["data"]["eot_subdomains_url"],
  "--parents=%s" % DOMAINS
]

# Run these scanners over *all* (which is a lot) discovered subdomains.
SUBDOMAIN_SCANNERS = "pshtt,sslyze"


# Options:
# --date: override date, defaults to contents of meta.json
# --scan=[skip,download,here]
#     skip: skip all scanning, assume CSVs are locally cached
#     download: download scan data from S3
#     here: run the default full scan
# --upload: upload scan data and resulting db.json anything to S3

def run(options):
  # Definitive scan date for the run.
  today = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")

  # 1. Download scan data, do a new scan, or skip altogether.
  scan_mode = options.get("scan", "skip")
  if scan_mode == "here":
    # 1a. Gather .gov federal subdomains.
    print("Gathering subdomains.")
    print()
    gather_subdomains(options)
    print()
    print("Subdomain gathering complete.")
    print()

    # 1b. Run (limited) scanning on these subdomains.
    print("Scanning subdomains with: %s" % SUBDOMAIN_SCANNERS)
    print()
    scan_subdomains(options)
    print()
    print("Subdomain scanning complete")
    print()

    # 1c. Run (broad) scanning on parent domains.
    print("Scanning parent domains.")
    print()
    scan_parents(options)
    print()
    print("Scan of parent domains complete.")
  elif scan_mode == "download":
    print("Downloading latest production scan data from S3.")
    print()
    live_scanned = "s3://%s/live/scan/" % (BUCKET_NAME)
    shell_out(["aws", "s3", "sync", live_scanned, SCANNED_DATA])
    print()
    print("Download complete.")

  # Sanity check to make sure we have what we need.
  if not os.path.exists(os.path.join(SCANNED_DATA, "meta.json")):
    print("No scan metadata downloaded, aborting.")
    exit()

  # Date can be overridden if need be, but defaults to meta.json.
  if options.get("date", None) is not None:
    the_date = options.get("date")
  else:
    # depends on YYYY-MM-DD coming first in meta.json time format
    scan_meta = ujson.load(open("data/output/parents/results/meta.json"))
    the_date = scan_meta['start_time'][0:10]


  # 2. Process and load data into Pulse's database.
  print("[%s] Loading data into Pulse." % the_date)
  print()
  data.processing.run(the_date)
  print()
  print("[%s] Data now loaded into Pulse." % the_date)

  # 3. Upload data to S3 (if requested).
  if options.get("upload", False):
    print("[%s] Syncing scan data and database to S3." % the_date)
    print()
    upload(the_date)
    print()
    print("[%s] Scan data and database now in S3." % the_date)

  print("[%s] All done." % the_date)


# Upload the scan + processed data to /live/ and /archive/ locations by date.
def upload(date):
  live_parents = "s3://%s/live/parents/" % (BUCKET_NAME)
  live_subdomains = "s3://%s/live/all/" % (BUCKET_NAME)
  live_db = "s3://%s/live/db/" % (BUCKET_NAME)
  archive_subdomains = "s3://%s/archive/%s/all/" % (BUCKET_NAME, date)
  archive_parents = "s3://%s/archive/%s/parents/" % (BUCKET_NAME, date)
  archive_db = "s3://%s/archive/%s/db/" % (BUCKET_NAME, date)

  acl = "--acl=public-read"

  shell_out(["aws", "s3", "sync", PARENTS_DATA, live_scanned, acl])
  shell_out(["aws", "s3", "sync", ALL_DATA, live_subdomains, acl])
  shell_out(["aws", "s3", "cp", DB_DATA, live_db, acl])

  # Ask S3 to do the copying, to save on time and bandwidth
  shell_out(["aws", "s3", "sync", live_scanned, archive_scanned, acl])
  shell_out(["aws", "s3", "sync", live_subdomains, archive_subdomains, acl])
  shell_out(["aws", "s3", "sync", live_db, archive_db, acl])


# Use domain-scan to scan .gov domains from the set domain URL.
# Drop the output into data/output/parents/results.
def scan_parents(options):
  scanners = "--scan=%s" % SCANNERS
  analytics = "--analytics=%s" % ANALYTICS_URL
  output = "--output=%s" % PARENTS_DATA
  a11y_redirects = "--a11y_redirects=%s" % A11Y_REDIRECTS
  a11y_config = "--a11y_config=%s" % A11Y_CONFIG

  full_command =[
    SCAN_COMMAND, DOMAINS,
    scanners,
    analytics, a11y_config, a11y_redirects,
    output,
    "--debug",
    "--sort"
  ]

  # In debug mode, use cached data, and allow easy Ctrl-C.
  if options.get("debug"):
    full_command += ["--serial"]

  # In real mode, ignore cached data, and parallelize.
  else:
    full_command += ["--force"]

  shell_out(full_command)

# Use domain-scan to gather .gov domains from public sources.
def gather_subdomains(options):
  print("[gather] Gathering subdomains.")

  full_command = [GATHER_COMMAND]

  full_command += [",".join(GATHERER_NAMES)]
  full_command += GATHERER_OPTIONS

  # Common to all gatherers.
  # --parents gets auto-included as its own gatherer source.
  full_command += [
    "--output=%s" % ALL_DATA_GATHERED,
    "--suffix=%s" % GATHER_SUFFIX,
    "--sort",
    "--debug"
  ]

  # In debug mode, allow cached data.
  if not options.get("debug"):
    full_command += ["--force"]

  shell_out(full_command)


# Run pshtt on each gathered set of subdomains.
def scan_subdomains(options):
  print("[scan] Scanning subdomains.")

  subdomains = os.path.join(ALL_DATA_GATHERED, "results", "gathered.csv")

  full_command = [
    SCAN_COMMAND,
    subdomains,
    "--scan=%s" % SUBDOMAIN_SCANNERS,
    "--output=%s" % ALL_DATA_SCANNED,
    "--debug",
    "--sort"
  ]

  # In debug mode, use cached data, and allow easy Ctrl-C.
  if options.get("debug"):
    full_command += ["--serial"]

  # In real mode, ignore cached data, and parallelize.
  else:
    full_command += ["--force"]

  shell_out(full_command)



## Utils function for shelling out.

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

# Quick and dirty CLI options parser.
def options():
  options = {}
  for arg in sys.argv[1:]:
    if arg.startswith("--"):

      if "=" in arg:
        key, value = arg.split('=')
      else:
        key, value = arg, "true"

      key = key.split("--")[1]
      key = key.lower()
      value = value.lower()

      if value == 'true': value = True
      elif value == 'false': value = False
      options[key] = value

  return options


### Run when executed.

if __name__ == '__main__':
    run(options())
