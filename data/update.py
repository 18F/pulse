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
#    - TODO: How should an admin be notified of an error?
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
DB_DATA = os.path.join(this_dir, "./db.json")
BUCKET_NAME = "pulse.cio.gov"

# domain-scan information
SCAN_TARGET = os.path.join(this_dir, "./output/scan")
SCAN_COMMAND = os.environ.get("DOMAIN_SCAN_PATH", None)
SCANNERS = os.environ.get("SCANNERS", "inspect,analytics,sslyze,tls")
ANALYTICS_URL = os.environ.get("ANALYTICS_URL", META["data"]["analytics_url"])

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

  # Download scan data, do a new scan, or skip altogether.
  scan_mode = options.get("scan", "skip")
  if scan_mode == "here":
    print("Kicking off a scan.")
    print()
    scan()
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
  archive_scanned = "s3://%s/archive/%s/scan/" % (BUCKET_NAME, date)
  archive_cached = "s3://%s/archive/%s/cache/" % (BUCKET_NAME, date)
  archive_db = "s3://%s/archive/%s/db/" % (BUCKET_NAME, date)

  acl = "--acl=public-read"

  shell_out(["aws", "s3", "sync", SCANNED_DATA, live_scanned, acl])
  shell_out(["aws", "s3", "sync", CACHE_DATA, live_cached, acl])
  shell_out(["aws", "s3", "cp", DB_DATA, live_db, acl])

  # Ask S3 to do the copying, to save on time and bandwidth
  shell_out(["aws", "s3", "sync", live_scanned, archive_scanned, acl])
  shell_out(["aws", "s3", "sync", live_cached, archive_cached, acl])
  shell_out(["aws", "s3", "cp", live_db, archive_db, acl])


# Use domain-scan to scan .gov domains from the set domain URL.
# Drop the output into data/output/scan/results.
def scan():
  scanners = "--scan=%s" % SCANNERS
  analytics = "--analytics=%s" % ANALYTICS_URL
  output = "--output=%s" % SCAN_TARGET

  shell_out([
    SCAN_COMMAND, DOMAINS,
    scanners, analytics, output,
    "--debug",
    "--force",
    "--sort",
    #"--serial",
  ])


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
