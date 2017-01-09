_[Return to the README](https://github.com/18F/pulse#readme)_

## Ideas for new sections for the site

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
* [Look at what Ben tracked](http://ben.balter.com/2011/09/07/analysis-of-federal-executive-domains/) - [example](https://site-inspector.herokuapp.com/domains/state.gov)
* IPv6
* DNSSEC
* https://monitor.dnsops.gov/
* What else can we get from Verisign?
