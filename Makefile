scss ?= assets/scss/main.scss
css ?= assets/css/main.css

all: styles

run:
	python pulse.py

styles:
	sass $(scss):$(css)

watch:
	sass --watch $(scss):$(css)

clean:
	rm -f $(css)
