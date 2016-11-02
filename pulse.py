#!/usr/bin/env python

import os

from flask import Flask
from waitress import serve
app = Flask(__name__)

from app import views
views.register(app)

from app import helpers
helpers.register(app)

port = int(os.getenv("PORT", 5000))
environment = os.getenv("PULSE_ENV", "development")

if environment == "development":
  app.debug = True

if __name__ == "__main__":
  if environment == "development":
    app.run(port=port)
  else:
    serve(app, port=port)
