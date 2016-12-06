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
#    - This takes ~25 hours with 1-process SSL Labs, as of 2016-01-24.
#    - Should drop results into data/output/scan (or a symlink).
#    - If exits with non-0 code, this should exit with non-0 code.
#
# 1a. Subdomains.
#    - Gather latest subdomains from public sources.
#    - Run pshtt, once for each source, on gathered subdomains.
#    - This creates 4 output directories. 2 gather, 2 scan (w/cache).
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

# post-processing and uploading information
SCANNED_DATA = os.path.join(this_dir, "./output/scan/results")
CACHE_DATA = os.path.join(this_dir, "./output/scan/cache")
SUBDOMAIN_DATA = os.path.join(this_dir, "./output/subdomains")
DB_DATA = os.path.join(this_dir, "./db.json")
BUCKET_NAME = "pulse.cio.gov"

# domain-scan information
SCAN_TARGET = os.path.join(this_dir, "./output/scan")
SCAN_COMMAND = os.environ.get("DOMAIN_SCAN_PATH", None)
SCANNERS = os.environ.get("SCANNERS", "pshtt,analytics,sslyze,inspect,tls")
ANALYTICS_URL = os.environ.get("ANALYTICS_URL", META["data"]["analytics_url"])

# subdomain gathering/scanning information
GATHER_TARGET = os.path.join(this_dir, "./output/subdomains/gather")
GATHER_COMMAND = os.environ.get("DOMAIN_GATHER_PATH", None)
GATHER_SUFFIX = ".gov"
GATHER_ANALYTICS_URL = META["data"]["analytics_subdomains_url"]
GATHER_PARENTS = DOMAINS  # Limit subdomains to set of base domains.
GATHERERS = [
  ["censys", "--export"],
  ["url", "--url=%s" % GATHER_ANALYTICS_URL]
]
SUBDOMAIN_SCAN_TARGET = os.path.join(this_dir, "./output/subdomains/scan")
SUBDOMAIN_SCANNERS = "pshtt"


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
    # 1a. Gather and scan subdomains.
    print("Kicking off subdomain gathering and scanning.")
    print()
    subdomains(options)
    print()
    print("Subdomain gathering and scan complete")
    print()

    print("Kicking off a scan.")
    print()
    scan(options)
    print()
    print("Domain-scan complete.")
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
    scan_meta = ujson.load(open("data/output/scan/results/meta.json"))
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
  live_scanned = "s3://%s/live/scan/" % (BUCKET_NAME)
  live_cached = "s3://%s/live/cache/" % (BUCKET_NAME)
  live_db = "s3://%s/live/db/" % (BUCKET_NAME)
  live_subdomains = "s3://%s/live/subdomains/" % (BUCKET_NAME)
  archive_scanned = "s3://%s/archive/%s/scan/" % (BUCKET_NAME, date)
  archive_cached = "s3://%s/archive/%s/cache/" % (BUCKET_NAME, date)
  archive_db = "s3://%s/archive/%s/db/" % (BUCKET_NAME, date)
  archive_subdomains = "s3://%s/archive/%s/subdomains/" % (BUCKET_NAME, date)

  acl = "--acl=public-read"

  shell_out(["aws", "s3", "sync", SCANNED_DATA, live_scanned, acl])
  shell_out(["aws", "s3", "sync", CACHE_DATA, live_cached, acl])
  shell_out(["aws", "s3", "sync", SUBDOMAIN_DATA, live_subdomains, acl])
  shell_out(["aws", "s3", "cp", DB_DATA, live_db, acl])

  # Ask S3 to do the copying, to save on time and bandwidth
  shell_out(["aws", "s3", "sync", live_scanned, archive_scanned, acl])
  shell_out(["aws", "s3", "sync", live_cached, archive_cached, acl])
  shell_out(["aws", "s3", "sync", live_subdomains, archive_subdomains, acl])
  shell_out(["aws", "s3", "sync", live_db, archive_db, acl])


# Use domain-scan to scan .gov domains from the set domain URL.
# Drop the output into data/output/scan/results.
def scan(options):
  scanners = "--scan=%s" % SCANNERS
  analytics = "--analytics=%s" % ANALYTICS_URL
  output = "--output=%s" % SCAN_TARGET

  full_command =[
    SCAN_COMMAND, DOMAINS,
    scanners, analytics, output,
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

# Use domain-scan to gather .gov hostnames from public sources.
# Then run pshtt on each gathered hostname.
def subdomains(options):

  # Use domain-scan to gather .gov domains from public sources.
  def gather_subdomains(gatherer, command):
    print("[%s][gather] Gathering subdomains." % gatherer)

    gatherer_output = os.path.join(GATHER_TARGET, gatherer)

    full_command = [GATHER_COMMAND]
    full_command += command

    # Common to all gatherers.
    full_command += [
      "--suffix=%s" % GATHER_SUFFIX,
      "--output=%s" % gatherer_output,
      "--parents=%s" % GATHER_PARENTS,
      "--sort",
      "--debug"
    ]

    # Debug mode, limit censys gathering to 1 page
    # (targeted at getting a small set of federal domains)
    if options.get("debug"):
      full_command += ["--end=200", "--start=200"]

    shell_out(full_command)


  # Run pshtt on each gathered set of subdomains.
  def scan_subdomains(gatherer):
    print("[%s][scan] Scanning subdomains." % gatherer)

    subdomains = os.path.join(GATHER_TARGET, gatherer, "results", ("%s.csv" % gatherer))
    scanner_output = os.path.join(SUBDOMAIN_SCAN_TARGET, gatherer)

    full_command = [
      SCAN_COMMAND,
      subdomains,
      "--scan=%s" % SUBDOMAIN_SCANNERS,
      "--output=%s" % scanner_output,
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


  for command in GATHERERS:
    gatherer = command[0]
    gather_subdomains(gatherer, command)
    scan_subdomains(gatherer)


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
