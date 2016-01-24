scss ?= static/scss/main.scss
css ?= static/css/main.css

all: styles

staging:
	cd deploy/ && fab deploy && cd ..

production:
	cd deploy/ && fab deploy --set environment=production && cd ..

run:
	python pulse.py

styles:
	sass $(scss):$(css)

watch:
	sass --watch $(scss):$(css)

clean:
	rm -f $(css)

# downloads latest snapshot of data locally
data_init:
	aws s3 sync s3://pulse.cio.gov/live/scan/ data/output/scan/results/
	aws s3 sync s3://pulse.cio.gov/live/processed/ data/output/processed/

# publishes data to S3 in the /live/ dir and a date-stamped directory
data_publish:
	aws s3 sync data/output/processed/ s3://pulse.cio.gov/live/processed/ --acl=public-read
	aws s3 sync data/output/scan/results/ s3://pulse.cio.gov/live/scan/ --acl=public-read
	aws s3 sync data/output/processed/ s3://pulse.cio.gov/archive/$(date +%Y-%m-%d)/processed/ --acl=public-read
	aws s3 sync data/output/scan/results/ s3://pulse.cio.gov/archive/$(date +%Y-%m-%d)/scan/ --acl=public-read
