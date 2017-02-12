scss ?= static/scss/main.scss
css ?= static/css/main.css

all: styles

staging:
	cd deploy/ && fab deploy --set environment=staging && cd ..

production:
	cd deploy/ && fab deploy --set environment=production && cd ..

# standalone push, don't download data (assume it's present)
cg_production_alone:
	cf login -a $$CF_API -u $$CF_USERNAME -p $$CF_PASSWORD -o gsa-ogp-pulse -s pulse && cf push pulse

# download data externally and then deploy to production
cg_production:
	make data_init && cf target -o gsa-ogp-pulse -s pulse && cf push pulse

cg_staging:
	make data_init && cf target -o gsa-ogp-pulse -s pulse && cf push pulse-staging

debug:
	DEBUG=true python pulse.py

styles:
	sass $(scss):$(css)

watch:
	sass --watch $(scss):$(css)

clean:
	rm -f $(css)

# Production data update process:
#
# Run a fresh scan, update the database, and upload data to S3.
update_production:
	python -m data.update --scan=here --upload

# Staging data update process:
#
# Download last production scan data, update the database.
update_staging:
	python -m data.update --scan=download

# Development data update process:
#
# Don't scan or download latest data (rely on local cache), update database.
update_development:
	python -m data.update --scan=skip

# downloads latest snapshot of data locally
# Pending cloud.gov production bucket:
# cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084
# Pending cloud.gov backup bucket:
# cg-72ce4caf-d81b-4771-9b96-3624b5554587
data_init:
	mkdir -p data/output/scan/results/
	curl https://s3-us-gov-west-1.amazonaws.com/cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084/live/scan/analytics.csv > data/output/scan/results/analytics.csv
	curl https://s3-us-gov-west-1.amazonaws.com/cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084/live/scan/pshtt.csv > data/output/scan/results/pshtt.csv
	curl https://s3-us-gov-west-1.amazonaws.com/cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084/live/scan/tls.csv > data/output/scan/results/tls.csv
	curl https://s3-us-gov-west-1.amazonaws.com/cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084/live/scan/sslyze.csv > data/output/scan/results/sslyze.csv
	curl https://s3-us-gov-west-1.amazonaws.com/cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084/live/scan/meta.json > data/output/scan/results/meta.json
	curl https://s3-us-gov-west-1.amazonaws.com/cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084/live/db/db.json > data/db.json
