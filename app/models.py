from tinydb import TinyDB, where
import os

this_dir = os.path.dirname(__file__)
db = TinyDB(os.path.join(this_dir, '../db.json'))

# These functions are meant to be the only ones that access the db
# directly. If we ever decide to migrate from tinydb, that can all be
# coordinated here.

# Data loads should clear the entire database first.
def clear_database():
  db.purge_tables()

class Report:
  # report_date (string, YYYY-MM-DD)
  # https.eligible (number)
  # https.uses (number, %)
  # https.enforces (number, %)
  # https.hsts (number, %)
  # analytics.eligible (number, %)
  # analytics.participates (number, %)

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


