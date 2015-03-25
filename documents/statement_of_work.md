
## Draft 

The .gov dashboard will be developed in several iterations, each with a focus on delivering at least one new usable functionality. Each iteration will focus on one or two areas of .gov policy, as described in the .gov policy memos. 

The first iterations will be focused on the "low-hanging fruit" of .gov policy, which is to say, the areas of .gov policy for which quantification structures already exist or could be developed with minimal time or effort. For the first iteration, there will be two pages: HTTPS and web analytics (Digital Analytics Program-derived or otherwise). 

The basic structure of the landing page will be a graphic with an overview of the agency's performance across all of metrics used in the dashboard, aggregated to show overall performance for all websites. We initially envision an interactive bar chart (including sorting capabilities, mouseover tooltips, etc.), though specific requirements for the graph will be described separately. In addition to the graph, there should be a tabbed browsing interface within the page that allows the user to change the view in order to concentrate on a specific policy area and should link to general implementation guidance. For version 1, there will be two tabs: HTTPS and Web Analytics. 

## Detailed Requirements

Initially, we aim to see the HTTPS page to be structured as follows: 
  * At the top of the page, an interactive graph displaying the performance across all websites for the metrics defined in the HTTPS subsection. 
  * Below the graphic, a report-card-style table displaying all of the .gov domains measured, with one row for each domain. The columns will each measure a separate sub-metric. The following is a list of columns: 
    * Domain name (index column)
    * Agency
    * Bureau/Component/Office (if applicable)
    * Is HTTPS Enforced?
    * Is HTTPS Present?
    * Does the site use HSTS? Including subdomains? If so, HSTS Pre-Load?
    * Possible ways to measure quality of SSL: 
     * SSL Labs grade? 
     * Strong forward secrecy? 
     * Latest version of TLS? 
     * Using old SSL Version (3.0)? 
     * Sha 1 vs Sha 2? (Perhaps this should be relegated to v2)
  * Each column in the table should have a mouseover tooltip with information about the metric, what it means, why it is important, and a link to a page that explains to what steps users can take to improve their agency's performance in the selected area. The individual data points should be colored conditionally according to their values (following a system of conditional formatting rules to be developed later) so that users can immediately target poorly-performing websites. 
  * Additionally, the following filters should be available: 
    * Agency
    * Bureau/Component/Office (if applicable)
    * Status (Live/Redirect/Inactive)
    * Domains/Subdomains

The Analytics page should have a structure similar to the HTTPS page, including the graphic and table with a similar look and feel. The columns in the Analytics table should be: 
 * Domain name (index column)
 * Agency
 * Bureau/Component/Office (if applicable)
 * Whether or not the domain uses DAP. 
 * Number of pages reported in the last 6 months.
 * Percentage of subdomains with analytics
 * Other analytics systems detected
