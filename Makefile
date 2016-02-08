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

# Runs the data update script.
update:
	python -m data.update

# downloads latest snapshot of data locally
data_init:
	mkdir -p data/output/scan/results/
	wget https://s3.amazonaws.com/pulse.cio.gov/live/scan/analytics.csv -O data/output/scan/results/analytics.csv
	wget https://s3.amazonaws.com/pulse.cio.gov/live/scan/inspect.csv -O data/output/scan/results/inspect.csv
	wget https://s3.amazonaws.com/pulse.cio.gov/live/scan/tls.csv -O data/output/scan/results/tls.csv
	wget https://s3.amazonaws.com/pulse.cio.gov/live/scan/meta.json -O data/output/scan/results/meta.json
	wget https://s3.amazonaws.com/pulse.cio.gov/live/db/db.json -O data/db.json
