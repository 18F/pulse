scss ?= assets/scss/main.scss
css ?= assets/css/main.css

all: styles

run:
	bundle exec jekyll serve

styles:
	bundle exec sass $(scss):$(css)

watch:
	bundle exec sass --watch $(scss):$(css)

clean:
	rm -f $(css)
