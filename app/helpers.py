import yaml
import datetime

def register(app):

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

  # TODO: consolidate data mappings in one place.
  # @app.template_filter('field_map')
  # def field_map(value, category=None, field=None):
  #     return data.data[category][field][str(value)]

  @app.template_filter('field_map')
  def field_map(value, category=None, field=None):
      return FIELD_MAPPING[category][field][value]

  @app.template_filter('percent')
  def percent(num, denom):
      return round((num / denom) * 100)

  @app.template_filter('percent_not')
  def percent_not(num, denom):
      return (100 - round((num / denom) * 100))
