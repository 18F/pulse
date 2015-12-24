
data = {
  'https': {

    'https': {
      "-1": "No",
      '0': "No", # (downgrade redirect)
      '1': "Yes", # (with certificate chain issues)
      '2': "Yes"
    },

    'https_forced': {
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
    'dap': {
      '0': "No",
      '1': "Yes"
    }
  }
}
