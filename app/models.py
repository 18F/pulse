from tinydb import TinyDB, where, Query
import os
import io
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


class Report:
  # report_date (string, YYYY-MM-DD)
  # https.eligible (number)
  # https.uses (number)
  # https.enforces (number)
  # https.hsts (number)
  # analytics.eligible (number)
  # analytics.participates (number)

  # Initialize a report with a given date.
  def create(report_date):
    db.table('reports').insert({'report_date': report_date})

  # There's only ever one.
  def latest():
    reports = db.table('reports').all()
    if len(reports) > 0:
      return reports[0]
    else:
      return None

  # Update latest report's 'https' or 'analytics' value
  # with the values
  def update(data):

    # TODO: can't figure out how to match on all! Workaround.
    db.table('reports').update(data,
      where('report_date').exists()
    )

class Domain:
  # domain (string)
  # agency_slug (string)
  # agency_name (string)
  # branch (string, legislative/judicial/executive)
  #
  # live? (boolean)
  # redirect? (boolean)
  # canonical (string, URL)
  #
  # https: {
  #   [many things]
  # },
  # analytics: {
  #   participating? (boolean)
  # }
  #

  def create(data):
    return db.table('domains').insert(data)

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
    domains = db.table('domains').search(where('domain') == domain_name)
    if len(domains) > 0:
      return domains[0]
    else:
      return None

  def eligible(report_name):
    return db.table('domains').search(
      Query()[report_name].exists()
    )

  def eligible_for_agency(agency_slug, report_name):
    return db.table('domains').search(
      (Query()[report_name].exists()) &
      (where("agency_slug") == agency_slug)
    )

  def db():
    return db


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
        if FIELD_MAPPING.get(field):
          row.append(FIELD_MAPPING[field][domain[field]])
        else:
          row.append(domain[field])
      for field in CSV_FIELDS[report_type]:
        row.append(FIELD_MAPPING[report_type][field][domain[report_type][field]])
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
  #   grade (number, >= A-)
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
