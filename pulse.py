#!/usr/bin/env python

from flask import Flask
from flask import render_template
import yaml
import os
import json
import datetime


# Initialize app.
app = Flask(__name__)
app.debug = True

###
# Load the data into memory.
#

# TODO: Where am I getting this from now that these are in S3?
# TODO: Uncomment landing pages.
# agencies = json.load(open("static/data/agencies.json"))
# domains = json.load(open("static/data/domains.json"))
from app import data


###
# Context processors and filters.

# Make site metadata available everywhere.
meta = yaml.safe_load(open("meta.yml"))
@app.context_processor
def inject_meta():
    return dict(site=meta, now=datetime.datetime.utcnow)

@app.template_filter('date')
def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
    return value.strftime(format)

@app.template_filter('field_map')
def field_map(value, category=None, field=None):
    return data.data[category][field][str(value)]

@app.template_filter('analytics_map')
def analytics_map(value, field=None):
    return data.data['analytics'][field][str(value)]

###
# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/about/")
def about():
    return render_template("about.html")

@app.route("/https/domains/")
def https_domains():
    return render_template("https/domains.html")

@app.route("/https/agencies/")
def https_agencies():
    return render_template("https/agencies.html")

@app.route("/https/guidance/")
def https_guide():
    return render_template("https/guide.html")

@app.route("/analytics/domains/")
def analytics_domains():
    return render_template("analytics/domains.html")

@app.route("/analytics/agencies/")
def analytics_agencies():
    return render_template("analytics/agencies.html")

@app.route("/analytics/guidance/")
def analytics_guide():
    return render_template("analytics/guide.html")

# @app.route("/agency/<slug>")
# def agency(slug=None):
#     if agencies.get(slug) is None:
#         pass # TODO: 404

#     return render_template("agency.html", agency=agencies[slug])

# @app.route("/domain/<hostname>")
# def domain(hostname=None):
#     if domains.get(hostname) is None:
#         pass # TODO: 404

#     return render_template("domain.html", domain=domains[hostname])



###
# Boot it up.
if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", 5000)))
