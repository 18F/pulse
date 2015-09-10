#!/usr/bin/env python

from flask import Flask
from flask import render_template
import yaml
import datetime


# Initialize app.
app = Flask(__name__)
app.debug = True

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


### 
# Boot it up.
if __name__ == "__main__":
    app.run()
