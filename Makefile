scss ?= assets/scss/main.scss
css ?= assets/css/main.css

all: styles

styles:
	sass $(scss):$(css)

watch:
	sass --watch $(scss):$(css)

clean:
	rm -f $(css)
