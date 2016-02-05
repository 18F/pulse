
data = {
  'https': {

    'uses': {
      "-1": "No",
      '0': "No", # (downgrade redirect)
      '1': "Yes", # (with certificate chain issues)
      '2': "Yes"
    },

    'enforces': {
      '0': "", # N/A (no HTTPS)
      '1': "No", # Present, not default
      '2': "Yes", # Defaults eventually to HTTPS
      '3': "Yes" # Defaults eventually + redirects immediately
    },

    'hsts': {
      "-1": "", # N/A
      '0': "No", # No
      '1': "Yes", # HSTS on only that domain
      '2': "Yes", # HSTS on subdomains
      '3': "Yes, and preload-ready", # HSTS on subdomains + preload flag
      '4': "Yes, and preloaded" # In the HSTS preload list
    },

    'grade': {
      "-1": "",
      '0': "F",
      '1': "T",
      '2': "C",
      '3': "B",
      '4': "A-",
      '5': "A",
      '6': "A+"
    }
  },

  'analytics': {
    'participating': {
      '0': "No",
      '1': "Yes"
    }
  }
}

# Mapping report/domain/agency field names to display names.
LABELS = {
  # used in export CSVs
  'domain': 'Domain',
  'canonical': 'URL',
  'branch': 'Branch',
  'redirect': 'Redirect',
  'agency_name': 'Agency',

  'total_domains': 'Number of Domains',

  'https': {
    'uses': 'Uses HTTPS',
    'enforces': 'Enforces HTTPS',
    'hsts': 'Strict Transport Security (HSTS)',
    'grade': 'SSL Labs Grade',

    'hsts_age': 'HSTS max-age',
    'grade_agencies': 'SSL Labs (A- or higher)',
    'fs': 'Forward Secrecy',
    'rc4': 'RC4',
    'sig': 'Signature Algorithm',
    'ssl3': 'SSLv3',
    'tls12': 'TLSv1.2',
  },

  'analytics': {
    'participating': 'Participates in DAP?'
  }
}


### Stupid mapping sync.

"""
I don't like this at all, but to keep the presentation synced
between the front-end table, and the CSV we generate, this is
getting replicated to the JavaScript files in this repository,
and needs to be manually synced.

The refactor that takes away from DataTables should also prioritize
a cleaner way to DRY ("don't repeat yourself") this mess up.
"""
CSV_MAPPING = {

  'redirect': {
    False: "No",
    True: "Yes"
  },

  'https': {

    'uses': {
      -1: "No",
      0: "No",
      1: "Yes", # (with certificate chain issues)
      2: "Yes"
    },

    'enforces': {
      0: "", # N/A (no HTTPS)
      1: "No", # Present, not default
      2: "Yes", # Defaults eventually to HTTPS
      3: "Yes" # Defaults eventually + redirects immediately
    },

    'hsts': {
      -1: "", # N/A
      0: "No", # No
      1: "Yes", # HSTS on only that domain
      2: "Yes", # HSTS on subdomains
      3: "Yes, and preload-ready", # HSTS on subdomains + preload flag
      4: "Yes, and preloaded" # In the HSTS preload list
    },

    'grade': {
      -1: "",
      0: "F",
      1: "T",
      2: "C",
      3: "B",
      4: "A-",
      5: "A",
      6: "A+"
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
  'common': ['domain', 'canonical', 'branch', 'agency_name', 'redirect'],
  'https': ['uses',  'enforces', 'hsts', 'grade'],
  'analytics': ['participating']
}
