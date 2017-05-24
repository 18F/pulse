#!/usr/bin/env python

import os

from flask import Flask
from waitress import serve

import newrelic.agency_report
from cfenv import AppEnv()

app = Flask(__name__)

from app import views
views.register(app)

from app import helpers
helpers.register(app)

port = int(os.getenv("PORT", 5000))
environment = os.getenv("PULSE_ENV", "development")

if environment == "development":
  app.debug = True

# Configure newrelic
env = AppEnv()
app_name = os.environ.get('NEW_RELIC_APP_NAME')
license_key = env.get_credential('NEW_RELIC_LICENSE_KEY')

if app_name and license_key:
    nr_settings = newrelic.agent.global_settings()
    nr_settings.app_name = app_name
    nr_settings.license_key = license_key
    newrelic.agent.initialize()

if __name__ == "__main__":
  if environment == "development":
    app.run(port=port)
  else:
    serve(app, port=port)
