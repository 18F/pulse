from tinydb import TinyDB, where, Query
import os
import io
import datetime
import csv
from app.data import CSV_FIELDS, FIELD_MAPPING, LABELS

this_dir = os.path.dirname(__file__)
db = TinyDB(os.path.join(this_dir, '../data/db.json'))

# These functions are meant to be the only ones that access the db
# directly. If we ever decide to migrate from tinydb, that can all be
# coordinated here.

# Data loads should clear the entire database first.
def clear_database():
  db.purge_tables()

# convenience
q = Query()

class Report:
  # report_date (string, YYYY-MM-DD)
  # https.eligible (number)
  # https.uses (number)
  # https.enforces (number)
  # https.hsts (number)
  # https.bod (number)
  # analytics.eligible (number)
  # analytics.participates (number)

  # Initialize a report with a given date.
  def create(data):
    db.table('reports').insert(data)

  def report_time(report_date):
    return datetime.datetime.strptime(report_date, "%Y-%m-%d")

  # There's only ever one.
  def latest():
    reports = db.table('reports').all()
    if len(reports) > 0:
      return reports[0]
    else:
      return None


class Domain:
  # domain (string)
  # agency_slug (string)
  # is_parent (boolean)
  #
  # agency_name (string)
  # branch (string, legislative/judicial/executive)
  #
  # parent_domain (string)
  # sources (array of strings)
  #
  # live? (boolean)
  # redirect? (boolean)
  # canonical (string, URL)
  #
  # totals: {
  #   https: { ... }
  #   crypto: { ... }
  # }
  #
  # https: { ... }
  # analytics: { ... }
  #

  def create(data):
    return db.table('domains').insert(data)

  def create_all(iterable):
    return db.table('domains').insert_multiple(iterable)


  def update(domain_name, data):
    return db.table('domains').update(
      data,
      where('domain') == domain_name
    )

  def add_report(domain_name, report_name, report):
    return db.table('domains').update(
      {
        report_name: report
      },
      where('domain') == domain_name
    )

  def find(domain_name):
    return db.table('domains').get(q.domain == domain_name)

  # Useful when you want to pull in all domain entries as peers,
  # such as reports which only look at parent domains, or
  # a flat CSV of all hostnames that match a report.
  def eligible(report_name):
    return db.table('domains').search(
      Query()[report_name]['eligible'] == True
    )

  # Useful when you have mixed parent/subdomain reporting,
  # used for HTTPS but not yet others.
  def eligible_parents(report_name):
    return db.table('domains').search(
      (Query()[report_name]['eligible_zone'] == True) &
      (where("is_parent") == True)
    )

  # Useful when you want to pull down subdomains of a particular
  # parent domain. Used for HTTPS expanded reports.
  def eligible_for_domain(domain, report_name):
    return db.table('domains').search(
      (Query()[report_name]['eligible'] == True) &
      (where("base_domain") == domain)
    )

  def db():
    return db

  def all():
    return db.table('domains').all()

  def to_csv(domains, report_type):
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)

    # initialize with a header row
    header = []
    for field in CSV_FIELDS['common']:
      header.append(LABELS[field])
    for field in CSV_FIELDS[report_type]:
      header.append(LABELS[report_type][field])
    writer.writerow(header)

    for domain in domains:
      row = []
      for field in CSV_FIELDS['common']:

        # Map some values, e.g. 1 -> "Yes", etc.
        if FIELD_MAPPING.get(field):
          row.append(FIELD_MAPPING[field][domain[field]])

        # Otherwise just use the raw value
        else:
          value = domain[field]

          # if it's a list, convert it to a list of strings and join
          if type(value) is list:
            value = [str(x) for x in value]
            value = ", ".join(value)

          row.append(value)

      # Currently, all report-specific fields use a mapping
      for field in CSV_FIELDS[report_type]:
        value = domain[report_type][field]
        mapped_value = FIELD_MAPPING[report_type][field][value]
        row.append(mapped_value)

      writer.writerow(row)

    return output.getvalue()


class Agency:
  # agency_slug (string)
  # agency_name (string)
  # branch (string)
  # total_domains (number)
  #
  # https {
  #   eligible (number)
  #   uses (number)
  #   enforces (number)
  #   hsts (number)
  #   modern (number)
  #   preloaded (number)
  # }
  # analytics {
  #   eligible (number)
  #   participating (number)
  # }
  #

  # An agency which had at least 1 eligible domain.
  def eligible(report_name):
    return db.table('agencies').search(
      Query()[report_name]['eligible'] > 0
    )

  # Create a new Agency record with a given name, slug, and total domain count.
  def create(data):
    return db.table('agencies').insert(data)

  def create_all(iterable):
    return db.table('agencies').insert_multiple(iterable)

  # For a given agency, add a report.
  def add_report(slug, report_name, report):
    return db.table('agencies').update(
      {
        report_name: report
      },
      where('slug') == slug
    )

  def find(slug):
    agencies = db.table('agencies').search(where('slug') == slug)
    if len(agencies) > 0:
      return agencies[0]
    else:
      return None

  def all():
    return db.table('agencies').all()
