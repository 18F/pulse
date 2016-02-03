
from flask import render_template, Response
from app import models
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
  @app.route("/data/domains/<report_name>.json")
  def domain_report(report_name):
    domains = models.Domain.eligible(report_name)
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

