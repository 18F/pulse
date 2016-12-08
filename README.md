[![Code Climate](https://codeclimate.com/github/18F/pulse/badges/gpa.svg)](https://codeclimate.com/github/18F/pulse) [![Build Status](https://travis-ci.org/18F/pulse.png)](https://travis-ci.org/18F/pulse) [![Dependency Status](https://gemnasium.com/badges/github.com/18F/pulse.svg)](https://gemnasium.com/github.com/18F/pulse)


## The pulse of the federal .gov webspace

How the .gov domain space is doing at best practices and federal requirements.

Other forks of the project in use include:

* https://nrkbeta.no/https-norge/
* https://https.jetzt
* https://govuk.jamiemagee.co.uk/
* https://pulse.openstate.eu/


## Setup

Pulse is a [Flask](http://flask.pocoo.org/) app written in **Python 3**. We recommend [pyenv](https://github.com/yyuu/pyenv) for easy Python version management.

* Install dependencies:

```bash
pip install -r requirements.txt
```

* If developing the stylesheets, you will also need [Sass](http://sass-lang.com/), [Bourbon](http://bourbon.io/), [Neat](http://neat.bourbon.io/), and [Bitters](http://bitters.bourbon.io/).

```bash
gem install sass bourbon neat bitters
```

* If editing styles during development, keep the Sass auto-compiling with:

```bash
make watch
```

* And to run the app in development, use:

```bash
make debug
```

This will run the app with `DEBUG` mode on, showing full error messages in-browser when they occur.

### Initializing dataset

To initialize the dataset with the last production scan data and database, there's a convenience function:

```
make data_init
```

This will download (using `curl`) the current live production database and scan data to the local `data/` directory.

## Deploying the site

The site can be easily deployed (by someone with credentials to the right server) through [Fabric](https://github.com/fabric/fabric), which requires Python 2.

The Fabric script will expect a defined `ssh` configuration called `pulse`, which you should already have defined in your SSH configuration with the right hostname and key.

To deploy to staging, switch to a Python 2 virtualenv with `fabric` installed, and run:

```
make staging
```

This will `cd` into `deploy/` and run `fab deploy`.

To deploy to production, activate Python 2 and `fabric` and run:

```
make production
```

This will run the fabric command to deploy to production.

## Updating the data in Pulse

The command to update the data in Pulse and publish it to production is simple:

```
python -m data.update
```

**But you will need to do some setup first.**

### Install domain-scan and dependencies

Download and set up `domain-scan` [from GitHub](https://github.com/18F/domain-scan).

`domain-scan` in turn requires [`pshtt`](https://github.com/dhs-ncats/pshtt) and [`ssllabs-scan`](https://github.com/ssllabs/ssllabs-scan). These currently both need to be cloned from GitHub and set up individually.

Pulse requires you to set one environment variable:

* `DOMAIN_SCAN_PATH`: A path to `domain-scan`'s `scan` binary.

However, `domain-scan` may need you to set a couple others if the binaries it uses aren't on your path:

* `PSHTT_PATH`: Path to the `pshtt_cli` binary.
* `SSLLABS_PATH`: Path to the `ssllabs-scan` binary.

### Configure the AWS CLI

To publish the resulting data to the production S3 bucket, install the official AWS CLI:

```
pip install awscli
```

And link it to AWS credentials that allow authorized write access to the `pulse.cio.gov` S3 bucket.

### Then run it

From the Pulse root directory:

```
python -m data.update
```

This will kick off the `domain-scan` scanning process for HTTP/HTTPS and DAP participation, using the `.gov` domain list as specified in `meta.yml` for the base set of domains to scan.

Then it will run the scan data through post-processing to produce some JSON and CSV files the Pulse front-end uses to render data.

Finally, this data will be uploaded to the production S3 bucket.

## Ideas for later versions

This project is an initial pass - there is much more information that can be represented in dashboards to great effect.  Below are some of the further ideas for both for future work on this project.  Feel free to add your ideas here, too.

* For the DAP Dashboard
  * Number of pages from a domain reporting into DAP
  * Page Status (e.g. 200, 404, etc) of all of the required urls in the [OMB website memo](https://www.whitehouse.gov/sites/default/files/omb/memoranda/2017/m-17-06.pdf).  
    * Potentially including subcomponents such as robots.txt
  * Number or list of subdomains from a domain reporting into DAP
  * Test the deeper config options that the DAP snippet should be employing, such as IP anonymization, Event tracking, Demographics turned off, and ?????.  (Possibly using headless browser)
* Does the site require “www”? Does it require not using “www”?
* Load time (server-side)
* More of the scans in [observatory.mozilla.org](https://observatory.mozilla.org)
* [Scan for SPF records](https://github.com/18F/pulse/issues/424)
* Mobile friendliness (poss. using Google's [Mobile Friendly Test](http://www.nextgov.com/mobile/2015/04/here-are-agency-websites-google-doesnt-think-are-mobile-friendly/110812/?oref=ng-relatedstories))
* Mixed content detection (linking to insecure resources)
* Use of third party services
* [STARTTLS email server encryption](https://github.com/18F/pulse/issues/218)
* 508 compliance (poss. with http://pa11y.org/)
* Any other items listed in the [OMB letter to OGP passing along .gov domain issuance](https://www.whitehouse.gov/sites/default/files/omb/egov/memo/policies-for-dot-gov-domain-issuance-for-federal-agency-public-websites.pdf)
* Lighter or fun things - like how many domains start with each letter of the alphabet, what the last 10 that came out were, etc.
* 2FA or Connect.gov ?  - Not sure how it would work but note Section 3's requirement [in this EO](https://www.whitehouse.gov/the-press-office/2014/10/17/executive-order-improving-security-consumer-financial-transactions)
* Anything from/with itdashboard.gov
* [Site hosting details](https://github.com/18F/pulse/issues/217)
* [open source](https://github.com/18F/pulse/issues/204)
* [Look at what Ben tracked](http://ben.balter.com/2011/09/07/analysis-of-federal-executive-domains/)
* IPv6
* DNSSEC
* https://monitor.dnsops.gov/
* What else can we get from Verisign?


### Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
