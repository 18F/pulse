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
