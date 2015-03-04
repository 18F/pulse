
# Model #1

## Version 1.0 
* Build a stable, public dataset of the underlying data
  * Could be an API but likely better as organized, static json files.  
  * The goal of this is to provide a stable data source that our projects can be built on, as well as a clear means by which the public can affirm the underlying data.  We also want third parties to be able to build similar applications.  
* Build a microsite that has: 
  * An HTTPS page 
  * An analytics page
* Host the microsite [at a .gov URL](https://github.com/GSA/dotgov-dashboard/issues/5).  

### HTTPs page
  * Agency
  * Domain
  * SSL: Yes/No
  * HTTPS Enforced: Yes/No
  * Certificate Age
  * HSTS: Yes/No
  * HSTS Pre-Load: Yes/No
  
Include the following filters: 
* Agency
* Status (Live/Redirect/Inactive) 
* Domains/Subdomains

### Analytics Page 
  * Agency
  * Domain
  * DAP Participant
  * Number of pages reported in last 6 months
  * Other detected analytics (e.g. Google Analytics, Omniture, Piwik) 

### Notes
* For HTTPS, does it make sense to leave off Inactive domains?  
* For Analytics, it would seem to make sense to leave off Redirecting and Inactive domains?  


