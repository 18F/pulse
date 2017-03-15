
1. Download the domain scan repo locally.  
2. Switch to the `make-lambda-optional` branch.  


======================


1. Download the domain scan repo locally.  
2. Switch to the `make-lambda-optional` branch.  
3a. Copy the [current federal dotgov list](https://github.com/GSA/data/blob/gh-pages/dotgov-domains/current-federal.csv) in the root of the local repo for domain scan (~/Documents/GitHub/domain-scan) and rename it domains.csv.  
3b. Referring to the [list of agencies with domains that make up the legislative, judicial, and non-federal agencies](https://github.com/18F/domain-scan/blob/make-lambda-optional/scripts/a11y/process_a11y.py#L20-L35), I manually edit the domains.csv file to remove domains that belong to those agencies.  
3c.  I have a list of [approximately 40 domains](https://github.com/18F/domain-scan/issues/110) that cause the scan to choke. I've confirmed multiple times that something in these domains stops the scan without generating results for these domains and forces me to restart the scan.  Therefore, I remove these domains from the domains.csv list.  
3d. Empty the cache and results folders (~/Documents/GitHub/domain-scan/cache and ~/Documents/GitHub/domain-scan/results).  
3e. In terminal, I change directory to the domain scan repo and run `docker-compose run scan domains.csv --scan=inspect --debug` (the inspect script from step 5).  This generates an inspect.csv file in the /results folder that I can then sort in order to find which domains are inactive or redirecting.  I then go through and manually remove them from the domains.csv file for two reasons - they have no place in the final results and also because if I didn't, the a11y.csv file would include error results from redirecting domains and then those domains would show up in the final result files.  
3f. I now have a domains.csv file that has been manually curated to remove domains from the other branches (because otherwise, they'd end up in the final results), proven problem domains, and inactive and redirecting domains.  
4. I again empty the cache and results folders (~/Documents/GitHub/domain-scan/cache and ~/Documents/GitHub/domain-scan/results).  
5. In terminal, I now run: `docker-compose run scan domains.csv --scan=inspect,a11y --debug`.    [Note [these](https://github.com/18F/domain-scan/blob/make-lambda-optional/scanners/a11y.py) [two](https://github.com/18F/domain-scan/blob/make-lambda-optional/scanners/inspect.py) scans]
  * This generates folders of cache results in /cache and `a11y.csv` and `inspect.csv` in /results. 
  * Unfortunately, the [ignore list](https://github.com/18F/domain-scan/blob/master/scanners/a11y.py#L65-L101) is not working in regards to the individual errors ([note spreadsheet](https://docs.google.com/spreadsheets/d/1IGpMCTzUZl4uavAsfyUPLjeUt227rKkKnmNMp0bpbkM/edit#gid=0)).  Therefore, I now need to go through the a11y.csv file and manually remove errors whose scans should have been excluded.  

Phase 2a (to generate the a11y.json file):  

_[Note - I first need to delete the Branch column in the domains.csv file I'm using (which is there b/c I'm using the DAP domains file)._  

6a. In terminal, run: `PYTHONPATH=. python scripts/a11y/process_a11y.py --a11y results/a11y.csv --domains domains.csv`.   [Note [this script](https://github.com/18F/domain-scan/blob/make-lambda-optional/scripts/a11y/process_a11y.py)].  
6b. This generates `domains.json`, `agencies.json`, and `a11y.json`.  I set aside the a11y.json file for later, but disregard the domains.json and agencies.json files since they don't factor in the problem domains, domains that failed to complete the pa11y scan but didn't choke it, and domains that don't actually have any errors.  This is because, right now, the files that are generated in this phase are just building off of the a11y.csv file and that is only composed of the individual errors results.  

Phase 2b (to generate the `domains.json`, `agencies.json` files):  

7a.  First - to generate a domains.json file, I need to create one with just the missing domains and no errors included.  To do that, I take the full domains list, then remove the domains that are in the domains.json generated in step 6a and 6b.  One easy method is to update a local copy of the site with the domains.json that has sites that have errors, and then use the web view of it to help me go through and generate an a11y.csv that has one spurious error for each that I can then go through and find/replace out.  

7b. I still need an agencies.json with correct arithmetic, but I think that the averages would work from the first conversion since it's looking at number of sites from the domains.csv.  Therefor, I just need to include the agencies that are missing with 0 error averages, which perhaps I do by hand as well.  

I get the list of missing agencies by comparing the list of agencies on the site currently with the the local site when I put in the agencies.json generated in 6b above. 



~~So... I'm actually going to hold on spelling out all of the steps, but basically, a whole lotta manual, funky steps going in to generating accurate `domains.json` and `agencies.json` files, which I then combine with the a11y.json file from after step 6a,~~ which are then overwritten in the [pulse repo](https://github.com/18F/pulse/tree/master/static/data/tables/accessibility) via PR ([ex.](https://github.com/18F/pulse/pull/581)), merged to master, and then staging is updated with the results.  
