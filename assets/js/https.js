$(document).ready(function () {

  $.get("/assets/data/tables/https-domains.json", function(data) {
    var prepared = prepareData(data.data);
    renderTable(prepared);
  });

  /**

    Filter out some rows, transform input rows to output rows.

    Example of incoming row:
    {
      "Domain": "consumerfinancial.gov",
      "Canonical": "http://www.consumerfinancial.gov",
      "Live": "True",
      "Redirect": "True",
      "Redirect To": "http://www.consumerfinance.gov/",
      "Valid HTTPS": "False",
      "Defaults to HTTPS": "False",
      "Downgrades HTTPS": "False",
      "Strictly Forces HTTPS": "False",
      "HTTPS Bad Chain": "False",
      "HTTPS Bad Hostname": "True",
      "HSTS": "False",
      "HSTS Header": "",
      "HSTS All Subdomains": "False",
      "HSTS Preload Ready": "False",
      "Broken Root": "False",
      "Broken WWW": "False"
    }

    Example of outgoing row:

    {
      "Domain": [domain],
      "HTTPS": [ "Yes" | "Yes, with issues" | "No" ],
      "HTTPS Behavior": [
        "N/A" | "Downgrade" | "Present" |
        "Default" | "Strict Default"
      ],
      "HSTS": [
        "N/A" | "None" | "Partial" |
        "Nearly Complete" | "Complete"
      ]
    }
  */

  // TODO: This data should come from the JSON, not the CSV -> JSON.
  var prepareData = function(domains) {
    var prepared = [];
    for (var i=0; i<domains.length; i++) {
      var domain = domains[i];

      // TODO: Maybe this should also be in the data pipeline, not JS.
      // Transform step:
      var row = {
        "Domain": domain["Domain"]
      };

      // HTTPS Presence:
      // Is it there? There for most clients? Not there?

      var https;

      if (domain["Valid HTTPS"] == "True")
        https = "Yes";
      else if (domain["HTTPS Bad Chain"] == "True")
        https = "Yes, with Issues";
      else
        https = "No";

      row["HTTPS"] = https;


      // HTTPS Behavior:
      // Characterize the HTTPS setup on the domain.
      var behavior;

      if (https == "No")
        behavior = "N/A";

      else {
      // "Downgrade" means HTTPS redirects to HTTP.
        if (domain["Downgrades HTTPS"] == "True")
          behavior = "Downgrade";

        // "Strict Default" means HTTP immediately redirects to HTTPS,
        // *and* that HTTP eventually redirects to HTTPS.
        else if (
          (domain["Strictly Forces HTTPS"] == "True") &&
          (domain["Defaults to HTTPS"] == "True")
        )
          behavior = "Strict Default";

        // "Default" means HTTP eventually redirects to HTTPS.
        else if (
          (domain["Strictly Forces HTTPS"] == "False") &&
          (domain["Defaults to HTTPS"] == "True")
        )
          behavior = "Default";

        // Either both are False, or just 'Strict Force' is True,
        // which doesn't matter on its own.
        else
          behavior = "Present";
      }

      row["HTTPS Behavior"] = behavior;


      // HSTS:
      // Characterize the presence and completeness of HSTS.
      var hsts;

      if (https == "No")
        hsts = "N/A";

      else {

        if (domain["HSTS"] == "False")
          hsts = "None";

        // "Complete" means HSTS preload ready (long max-age).
        else if (domain["HSTS Preload Ready"] == "True")
          hsts = "Complete";

        // "Nearly Complete" means `includeSubdomains`, but no `preload`.
        else if (domain["HSTS All Subdomains"] == "True")
          hsts = "Nearly Complete";

        // "Partial" means HSTS, but not on subdomains.
        else // if (domain["HSTS"] == "True")
          hsts = "Partial";

      }

      row["HSTS"] = hsts;

      prepared.push(row)
    }

    return prepared;
  };

  var renderTable = function(data) {
    $("table").DataTable({

      data: data,

      columns: [
        {"data":"Domain"},
        {"data":"HTTPS"},
        {"data":"HTTPS Behavior"},
        {"data":"HSTS"}
      ],

      dom: "lrtip"
    });
  };

})