
# Mapping report/domain/agency field names to display names.
LABELS = {
  # used in export CSVs
  'domain': 'Domain',
  'canonical': 'URL',
  'branch': 'Branch',
  'redirect': 'Redirect',
  'agency_name': 'Agency',
  'base': 'Base Domain',
  'source': 'Sources',

  'total_domains': 'Number of Domains',

  'https': {
    'uses': 'Uses HTTPS',
    'enforces': 'Enforces HTTPS',
    'hsts': 'Strict Transport Security (HSTS)',
    'preloaded': 'Preloaded (recommended)',
    'bod_crypto': 'BOD 18-01 Requirements',

    'hsts_age': 'HSTS max-age',
    'bod_agencies': 'BOD 18-01 Requirements',
    '3des': '3DES',
    'rc4': 'RC4',
    'ssl3': 'SSLv3',
    'tls12': 'TLSv1.2',
  },

  'analytics': {
    'participating': 'Participates in DAP?'
  }
}


FIELD_MAPPING = {

  'redirect': {
    False: "No",
    True: "Yes"
  },

  'https': {

    'uses': {
      -1: "No",
      0: "No",  # Downgrades HTTPS -> HTTP
      1: "Yes", # (with certificate chain issues)
      2: "Yes"
    },

    'enforces': {
      0: "",  # N/A (no HTTPS)
      1: "No",  # Present, not default
      2: "Yes",  # Defaults eventually to HTTPS
      3: "Yes"  # Defaults eventually + redirects immediately
    },

    'hsts': {
      -1: "",  # N/A
      0: "No",  # No
      1: "No",  # No, HSTS with short max-age (for canonical endpoint)
      2: "Yes",  # Yes, HSTS for >= 1 year (for canonical endpoint)
    },

    'preloaded': {
      0: "",  # No (leave blank, since not required)
      1: "Ready",  # Preload-ready
      2: "Yes"  # Yes
    },

    'bod_crypto': {
      -1: "",
      0: "No",
      1: "Yes"
    }
  },

  'analytics': {
    'participating': {
      False: "No",
      True: "Yes"
    }
  }
}

CSV_FIELDS = {
  'common': ['domain', 'base', 'canonical', 'agency_name', 'sources'],
  'https': ['uses', 'enforces', 'hsts', 'preloaded', 'bod_crypto'],
  'analytics': ['participating']
}
