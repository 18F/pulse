
from flask import render_template, Response
from app import models
from app.data import FIELD_MAPPING
import ujson

def register(app):

  @app.route("/")
  def index():
      return render_template("index.html")

  @app.route("/about/")
  def about():
      return render_template("about.html")

  ##
  # Data endpoints.

  # High-level %'s, used to power the donuts.
  @app.route("/data/reports/<report_name>.json")
  def report(report_name):
    response = Response(ujson.dumps(models.Report.latest().get(report_name, {})))
    response.headers['Content-Type'] = 'application/json'
    return response

  # Detailed data per-domain, used to power the data tables.
  @app.route("/data/domains/<report_name>.<ext>")
  def domain_report(report_name, ext):
    domains = models.Domain.eligible(report_name)

    if ext == "json":
      response = Response(ujson.dumps({'data': domains}))
      response.headers['Content-Type'] = 'application/json'
    elif ext == "csv":
      response = Response(models.Domain.to_csv(domains, report_name))
      response.headers['Content-Type'] = 'text/csv'
    return response

  @app.route("/data/agencies/<report_name>.json")
  def agency_report(report_name):
    domains = models.Agency.eligible(report_name)
    response = Response(ujson.dumps({'data': domains}))
    response.headers['Content-Type'] = 'application/json'
    return response

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

  @app.route("/agency/<slug>")
  def agency(slug=None):
      agency = models.Agency.find(slug)
      if agency is None:
          pass # TODO: 404

      return render_template("agency.html", agency=agency)

  @app.route("/domain/<hostname>")
  def domain(hostname=None):
      domain = models.Domain.find(hostname)
      if domain is None:
          pass # TODO: 404

      return render_template("domain.html", domain=domain)

  @app.route("/accessibility/domains/")
  def accessibility_domains():
    return render_template("accessibility/domains.html")

  @app.route("/accessibility/agencies/")
  def accessibility_agencies():
    return render_template("accessibility/agencies.html")

  @app.route("/accessibility/guidance/")
  def accessibility_guide():
    return render_template("accessibility/guide.html")


  @app.template_filter('field_map')
  def field_map(value, category=None, field=None):
      return FIELD_MAPPING[category][field][value]

  @app.template_filter('percent')
  def percent(num, denom):
    return round((num / denom) * 100)

  @app.template_filter('percent_not')
  def percent_not(num, denom):
    return (100 - round((num / denom) * 100))
