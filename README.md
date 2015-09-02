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

## Updating the data in Pulse

Updating Pulse is a multi-step process that combines data published by government offices with data scanned from the public internet.

##### Step 1: Get official data

The official `.gov` domain list is published quarterly in [this directory](https://github.com/GSA/data/tree/gh-pages/dotgov-domains). Download the `federal` CSV for the most recent date. This will be referred to below as **domains.csv**.

##### Step 2: Scan domains

Use [`domain-scan`](https://github.com/18F/domain-scan) to scan the `.gov` domain list, using the DAP list as a reference.

* Download and set up `domain-scan` [from GitHub](https://github.com/18F/domain-scan). For right now, this requires [`site-inspector`](https://rubygems.org/gems/site-inspector) **1.0.2** (not 2.0) and [`ssllabs-scan`](https://github.com/ssllabs/ssllabs-scan).

* Tell `domain-scan` to run the `inspect`, `tls`, and `analytics` scanners over the list of `.gov` domains, referencing the DAP participation list. Use `--force` to tell it to ignore any disk cache and to tell SSL Labs to ignore its server-side cache. Use `--sort` to sort the resulting CSV so that domains are in a consistent order.

The command for this might look like:

```bash
./scan domains.csv --scan=inspect,tls,analytics --analytics=https://analytics.usa.gov/data/live/second-level-domains.csv --output=domain-report --debug --force --sort
```

This will output a CSV report for each scanner to `domain-report/results/`.

##### Step 3: Update Pulse

Move the report CSVs into this repo, run a script to update Pulse's data, and mark the new date(s) in `_config.yml`.

* Copy `inspect.csv`, `tls.csv`, `analytics.csv` and `meta.json` into the `data/` directory of this repository.

* Update `_config.yml` to reflect the latest dates:

```yaml
data:
  domains: 2015-03-15
  dap: 2015-05-29
  scan: 2015-06-07
```

`domains`: The date the `.gov` domain list was *generated* by the `.gov` registry.

`dap`: The date the DAP participation list was *generated* by the Digital Analytics Program.

`scan`: The date that `domain-scan` was *executed* and which created `inspect.csv` and `tls.csv`.

* Update Pulse's data from the `data/` directory:

```bash
./update
```

This will use the scanned data to create the high-level conclusions Pulse displays to users and makes available for download.

* Review the changes, rebuild the site, and if all looks good, commit them to source control.


## Ideas for later versions

This project is an initial pass - there is much more information that can be represented in dashboards to great effect.  Below are some of the further ideas for both for future work on this project.  Feel free to add your ideas here, too.

* For the DAP Dashboard
  * Number of pages from a domain reporting into DAP
  * Number or list of subdomains from a domain reporting into DAP
  * Test the deeper config options that the DAP snippet should be employing, such as IP anonymization, Event tracking, Demographics turned off, and ?????.  (Possibly using headless browser)
* Does the site require “www”? Does it require not using “www”?
* Load time (server-side)
* Mobile friendliness (poss. using Google's [Mobile Friendly Test](http://www.nextgov.com/mobile/2015/04/here-are-agency-websites-google-doesnt-think-are-mobile-friendly/110812/?oref=ng-relatedstories))
* Mixed content detection (linking to insecure resources)
* Use of third party services
* 508 compliance (poss. with http://pa11y.org/)
* Any other items listed in the [OMB letter to OGP passing along .gov domain issuance](https://www.whitehouse.gov/sites/default/files/omb/egov/memo/policies-for-dot-gov-domain-issuance-for-federal-agency-public-websites.pdf)
* Lighter or fun things - like how many domains start with each letter of the alphabet, what the last 10 that came out were, etc.
* 2FA or Connect.gov ?  - Not sure how it would work but note Section 3's requirement [in this EO](https://www.whitehouse.gov/the-press-office/2014/10/17/executive-order-improving-security-consumer-financial-transactions)
* Anything from/with itdashboard.gov
* [open source](https://github.com/18F/pulse/issues/204)
* [Look at what Ben tracked](http://ben.balter.com/2011/09/07/analysis-of-federal-executive-domains/)
* IPv6
* DNSSEC
* What else can we get from Verisign?


### Public domain

This project is in the worldwide [public domain](LICENSE.md). As stated in [CONTRIBUTING](CONTRIBUTING.md):

> This project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
>
> All contributions to this project will be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
