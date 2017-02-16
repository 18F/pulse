The ATO process for this project is documented [here](https://pages.18f.gov/before-you-ship/ato/).

Here are major components, with links to the resulting artifacts:  

* [x] [Set up monitoring](https://pages.18f.gov/before-you-ship/infrastructure/monitoring/)
   - [x] [Downtime alerts](https://pages.18f.gov/before-you-ship/infrastructure/monitoring/#downtime) - Set to go to pulse@cio.gov
   - [x] [Error alerts](https://pages.18f.gov/before-you-ship/infrastructure/monitoring/#errors)
2. [x] Add an [`.about.yml`](https://github.com/18F/pulse/blob/master/.about.yml) for the main repository
3. [x] [Security scans](https://pages.18f.gov/before-you-ship/security/scanning/)
   - [x] Set up [static analysis](https://pages.18f.gov/before-you-ship/security/static-analysis/) service - [Code Climate](https://codeclimate.com/github/18F/pulse) | [Gemnasium](https://gemnasium.com/github.com/18F/pulse)
     - [x] Add service badges to [the README](https://github.com/18f/pulse#readme)
   - [x] [Perform dynamic vulnerability scanning](https://compliance-viewer.18f.gov/results/pulse/current)
     1. [x] Resolve any visible security issues, re-running the scan as needed
     2. [x] Add the issue-free scan report or [documentation about false positives](https://docs.google.com/document/d/1pRpb48GT1UyZpKKJlLRD4Oj2oaKMobXukzwby8ntZno/edit#) to the `ATOs` folder in Google Drive
4. [x] Update relevant documentation, primarily the README
5. [x] Add a [System Security Plan](https://github.com/18F/pulse/blob/master/system-security-plan.yml) to the repository
6. [x] [Set up Compliance Masonry documentation](https://github.com/18F/pulse/blob/master/compliance/component.yaml)
7. [ ] [Implement the controls](https://pages.18f.gov/before-you-ship/ato/walkthrough/#step-3--implement-the-controls)
