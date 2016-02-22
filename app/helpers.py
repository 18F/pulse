import yaml
import datetime
from app import models

# For use in templates.
def register(app):

  ###
  # Context processors and filters.

  def scan_date():
    return models.Report.report_time(models.Report.latest()['report_date'])

  # Make site metadata available everywhere.
  meta = yaml.safe_load(open("meta.yml"))
  @app.context_processor
  def inject_meta():
      return dict(site=meta, now=datetime.datetime.utcnow, scan_date=scan_date())

  @app.template_filter('date')
  def datetimeformat(value, format='%H:%M / %d-%m-%Y'):
      return value.strftime(format)

  @app.template_filter('field_map')
  def field_map(value, category=None, field=None):
      return FIELD_MAPPING[category][field][value]

  @app.template_filter('percent')
  def percent(num, denom):
      return round((num / denom) * 100)

  @app.template_filter('percent_not')
  def percent_not(num, denom):
      return (100 - round((num / denom) * 100))
