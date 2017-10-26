import os
import sys
import yaml

this_dir = os.path.dirname(__file__)

# App-level metadata.
META = yaml.safe_load(open(os.path.join(this_dir, "../meta.yml")))
DOMAINS = os.environ.get("DOMAINS", META["data"]["domains_url"])

# domain-scan paths (MUST be set in env)
SCAN_COMMAND = os.environ.get("DOMAIN_SCAN_PATH", None)
GATHER_COMMAND = os.environ.get("DOMAIN_GATHER_PATH", None)


# post-processing and uploading information
PARENTS_DATA = os.path.join(this_dir, "./output/parents")
PARENTS_RESULTS = os.path.join(this_dir, "./output/parents/results")
SUBDOMAIN_DATA = os.path.join(this_dir, "./output/subdomains")
SUBDOMAIN_DATA_GATHERED = os.path.join(this_dir, "./output/subdomains/gather")
SUBDOMAIN_DATA_SCANNED = os.path.join(this_dir, "./output/subdomains/scan")

DB_DATA = os.path.join(this_dir, "./db.json")
BUCKET_NAME = META['bucket']

# DAP source data
ANALYTICS_URL = META["data"]["analytics_url"]

# a11y source data
A11Y_CONFIG = META["a11y"]["config"]
A11Y_REDIRECTS = META["a11y"]["redirects"]

### Parent domain scanning information
#
SCANNERS = os.environ.get("SCANNERS", "pshtt,sslyze,analytics,a11y,third_parties")

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
