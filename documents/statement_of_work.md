

## Needs
* 2-3 paragraphs articulate what the first task order will entail

## Draft 

The .gov dashboard will be developed in several iterations, each with a focus on delivering at least one new usable functionality. Each iteration will focus on one or two areas of .gov policy, as described in the .gov policy memos. 

The first iterations will be focused on the "low-hanging fruit" of .gov policy, which is to say, the areas of .gov policy for which quantification structures already exist or could be developed with minimal time or effort. For the first iteration, there will be two pages: HTTPS and web analytics (DAP or otherwise). 

The basic structure of the landing page will be a graphic with an overview of the agency's performance across all of metrics used in the dashboard, aggregated to show overall performance for all websites. We initially envision an interactive bar chart (including sorting capabilities, mouseover tooltips, etc.), though specific requirements for the graph will be described separately. In addition to the graph, there should be a tabbed browsing interface within the page that allows the user to change the view in order to concentrate on a specific policy area. For version 1, there will be two tabs: HTTPS and Web Analytics. 

Initially, we aim to see the HTTPS page to be structured as follows: 
  * At the top of the page, an interactive graph displaying the performance across all websites for the metrics defined in the HTTPS subsection. 
  * Below the graphic, a report-card-style table displaying all of the .gov domains measured, with one row for each domain. The columns will each measure a separate sub-metric. The list of sub-metrics is: 
    * Is HTTPS Enforced?
    * Does the site use SSL?
    * How old is the site's certificate?
    * Does the site use HSTS? If so, HSTS Pre-Load?
  * Each column in the table should have a mouseover tooltip with information about the metric, what it means, why it is important, and a link to a page that explains to CIOs what steps they can take to improve their agency's performance in the selected area
  * Additionally, the following filters should be available: 
    * Agency
    * Status (Live/Redirect/Inactive)
    * Domains/Subdomains
