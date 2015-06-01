## The pulse of the federal .gov webspace

How the .gov domain space is doing at best practices and federal requirements.

## Setup

* Install Bundler if necessary, then install dependencies:

```bash
gem install bundler
bundle install
```

* Now you can run the app:

```bash
make run
```

* If editing styles during development, keep the Sass auto-compiling with:

```bash
make watch
```

## Ideas for later versions

This project is an initial pass - there is mmuch more information that can be represented in dashboards to great effect.  Below are some of the further ideas for both for future work on this project.  Feel free to add your ideas here, too.

* For the HTTPS Dashboard:
  * Even more HTTPS detail, e.g. SHA-1, forward secrecy
  * Expand to cover subdomains
* For the DAP Dashboard
  * Number of pages from a domain reporting into DAP
  * Number or list of subdomains from a domain reporting into DAP
  * Expand to cover subdomains
  * Test the deeper config options that the DAP snippet should be employing, such as IP anonymization, Event tracking, Demographics turned off, and ?????.  (Possibly using headless browser)
* Does the site require “www”? Does it require not using “www”?
* Load time (server-side)
* Mobile friendliness (poss. using Google's [Mobile Friendly Test](http://www.nextgov.com/mobile/2015/04/here-are-agency-websites-google-doesnt-think-are-mobile-friendly/110812/?oref=ng-relatedstories))
* Mixed content detection (linking to insecure resources)
* Use of third party services
* 508 compliance (poss. with http://pa11y.org/)
* Any other items listed in the [OMB letter to OGP passing along .gov domain issuance](https://www.whitehouse.gov/sites/default/files/omb/egov/memo/policies-for-dot-gov-domain-issuance-for-federal-agency-public-websites.pdf)
* Lighter or fun things - like how many domains start with each letter of the alphabet, what the last 10 that came out were, etc.  

### Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
