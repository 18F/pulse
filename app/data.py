
# Mapping report/domain/agency field names to display names.
LABELS = {
  # used in export CSVs
  'common': {
    'domain': 'Domain',
    'canonical': 'URL',
    'branch': 'Branch',
    'agency_name': 'Agency',
    'base_domain': 'Base Domain',
    'sources': 'Sources',

    'total_domains': 'Number of Domains'
  },

  'https': {
    'uses': 'Uses HTTPS',
    'enforces': 'Enforces HTTPS',
    'hsts': 'Strict Transport Security (HSTS)',
    'preloaded': 'Preloaded',
    'bod_crypto': 'Free of RC4/3DES and SSLv2/SSLv3',
    'compliant': 'Compliant with M-15-13 and BOD 18-01',

    'hsts_age': 'HSTS max-age',
    'bod_agencies': 'Free of RC4/3DES and SSLv2/SSLv3',
    '3des': '3DES',
    'rc4': 'RC4',
    'sslv2': 'SSLv2',
    'sslv3': 'SSLv3'
  },

  'analytics': {
    'participating': 'Participates in DAP?'
  }
}


FIELD_MAPPING = {

  'common': {},

  'https': {

    'uses': {
      -1: "No",
      0: "No",  # Downgrades HTTPS -> HTTP
      1: "Yes", # (with certificate chain issues)
      2: "Yes"
    },

    'enforces': {
      0: "No",  # N/A (no HTTPS)
      1: "No",  # Present, not default
      2: "Yes",  # Defaults eventually to HTTPS
      3: "Yes"  # Defaults eventually + redirects immediately
    },

    'hsts': {
      -1: "No",  # N/A
      0: "No",  # No
      1: "No",  # No, HSTS with short max-age (for canonical endpoint)
      2: "Yes",  # Yes, HSTS for >= 1 year (for canonical endpoint)
      3: "Preloaded" # Yes, via preloading (subdomains only)
    },

    'preloaded': {
      0: "No",  # No
      1: "Ready",  # Preload-ready
      2: "Yes"  # Yes
    },

    'bod_crypto': {
      -1: "",
      0: "No",
      1: "Yes"
    }
  }
}

CSV_FIELDS = {
  'common': ['domain', 'base_domain', 'canonical', 'agency_name', 'sources'],
  'https': ['compliant', 'enforces', 'hsts', 'bod_crypto', '3des', 'rc4', 'sslv2', 'sslv3', 'preloaded'],
  'analytics': ['participating']
}
