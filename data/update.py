#!/usr/bin/env python

import subprocess
import datetime
import processing
import os
import yaml
import logging


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
# 2. Run processing.py to generate front-end-ready data.
#    - TODO: Slim down what this generates, make more server-generated.
#    - Will drop results into data/output/processed
#
# 3. TODO: Refresh application database with latest data.
#    - Likely to be SQLite.
#
# 4. Upload data to S3.
#    - Depends on the AWS CLI and access credentials already being configured.
#    - TODO: Stop uploading to /live/, make it server-generated.
#    - TODO: Consider moving from aws CLI to Python library.

this_dir = os.path.dirname(__file__)

# App-level metadata.
META = yaml.safe_load(open(os.path.join(this_dir, "../meta.yml")))
DOMAINS = os.environ.get("DOMAINS", META["data"]["domains_url"])

# post-processing and uploading information
SCANNED_DATA = os.path.join(this_dir, "./output/scan/results")
PROCESSED_DATA = os.path.join(this_dir, "./output/processed")
BUCKET_NAME = "pulse.cio.gov"

# domain-scan information
SCAN_TARGET = os.path.join(this_dir, "./output/scan")
SCAN_COMMAND = os.environ.get("DOMAIN_SCAN_PATH", None)
SCANNERS = os.environ.get("SCANNERS", "inspect,tls,analytics")
ANALYTICS_URL = "https://analytics.usa.gov/data/live/second-level-domains.csv"

def run():
  # Definitive scan date for the run.
  the_date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")

  # Kick off domain-scan.
  print("[%s] Kicking off a scan." % the_date)
  print()
  scan()
  print()
  print("[%s] Domain-scan complete." % the_date)

  # 2. Process scan data to be front-end-ready.
  print("[%s] Running Pulse post-processor." % the_date)
  print()
  processing.run()
  print()
  print("[%s] Processed data now in output/data/processed." % the_date)

  # TODO: Refresh application database.

  # 4. Upload data to S3.
  print("[%s] Syncing processed data to S3." % the_date)
  print()
  upload(the_date)
  print()
  print("[%s] Processed data now in S3." % the_date)

  print("[%s] All done." % the_date)


# Upload the scan + processed data to /live/ and /archive/ locations by date.
def upload(date):
  live_scanned = "s3://%s/live/scan/" % (BUCKET_NAME)
  live_processed = "s3://%s/live/processed/" % (BUCKET_NAME)
  archive_scanned = "s3://%s/archive/%s/scan/" % (BUCKET_NAME, date)
  archive_processed = "s3://%s/archive/%s/processed/" % (BUCKET_NAME, date)

  acl = "--acl=public-read"

  shell_out(["aws", "s3", "sync", SCANNED_DATA, live_scanned, acl])
  shell_out(["aws", "s3", "sync", PROCESSED_DATA, live_processed, acl])
  shell_out(["aws", "s3", "sync", SCANNED_DATA, archive_scanned, acl])
  shell_out(["aws", "s3", "sync", PROCESSED_DATA, archive_processed, acl])


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



### Run when executed.

if __name__ == '__main__':
    run()
