$(document).ready(function () {

  // referenced in a few places
  var table;

  $.get("/data/domains/https.json", function(data) {
    renderTable(data.data);
  });

  /**
  * I don't like this at all, but to keep the presentation synced
  * between the front-end table, and the CSV we generate, this is
  * getting replicated to the /data/update script in this repository,
  * and needs to be manually synced.
  *
  * The refactor that takes away from DataTables should also prioritize
  * a cleaner way to DRY (don't repeat yourself) this mess up.
  */

  var names = {

    enforces: {
      0: "No", // No (no HTTPS)
      1: "No", // Present, not default
      2: "Yes", // Defaults eventually to HTTPS
      3: "Yes" // Defaults eventually + redirects immediately
    },

    hsts: {
      "-1": "No", // No (no HTTPS)
      0: "No",  // No
      1: "No", // No, HSTS with short max-age (for canonical endpoint)
      2: "Yes" // Yes, HSTS for >= 1 year (for canonical endpoint)
    },

    bod_crypto: {
      "-1": "--", // No HTTPS
      0: "No",
      1: "Yes"
    },

    preloaded: {
      0: "No",  // No
      1: "Ready",  // Preload-ready
      2: "<strong>Yes</strong>"  // Yes
    }
  };

  var display = function(set) {
    return function(data, type, row) {
      if (type == "sort")
        return data.toString();
      else
        return set[data.toString()];
    }
  };

  var showNotes = function(data, type, row) {
    if (type == "sort") return null;

    if (row.https.preloaded)
      return "Preloaded";
    else
      return "Not yet preloaded.";
  }

  // Describe what's going on with this domain's subdomains.
  var showDetails = function(data, type, row) {
    if (type == "sort") return null;
    if (loneDomain(row)) return null;

    var eligible = row.totals.https.eligible;
    var services = (eligible == 1 ? "service" : "services");
    return "Load details for " + n("" + eligible + " " + services) + " on this domain. &raquo;";
  };

  var agencyDownloadFor = function(row) {
    return "https://s3-us-gov-west-1.amazonaws.com/cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084/live/subdomains/agencies/" + row["agency_slug"] + "/https.csv";
  };

  var loadSubdomainData = function(row, base_domain, response) {
    var subdomains = response.data;
    var all = [];

    for (i=0; i<subdomains.length; i++) {
      var subdomain = subdomains[i];
      var details = $("<tr/>").addClass("subdomain");

      var link = "<a href=\"" + subdomain.canonical + "\" target=\"blank\">" + Utils.truncate(subdomain.domain, 35) + "</a>";
      details.append($("<td/>").addClass("link").html(link));

      var https = names.enforces[subdomain.https.enforces];
      details.append($("<td/>").html(https));

      var hsts = names.hsts[subdomain.https.hsts];
      details.append($("<td/>").html(hsts));

      var crypto = names.bod_crypto[subdomain.https.bod_crypto];
      details.append($("<td/>").html(crypto));

      // blank
      details.append($("<td/>"));

      all.push(details);
    }

    row.child(all, "child").show();
  };

  // Construct a sentence explaining the HTTP situation.
  var zoneDetails = function(data, type, row) {

    if (type == "sort")
      return null;

    var https = row.https.uses;
    var behavior = row.https.enforces;
    var hsts = row.https.hsts;
    var hsts_age = row.https.hsts_age;
    var preloaded = row.https.preloaded;
    var crypto = row.https.bod_crypto;

    var details;

    // CASE: HSTS, but HTTPS not enforced.
    if ((https >= 1) && (behavior < 2) && (hsts == 2))
      details = "Domain uses " + l("hsts", "HSTS") + ", but is not redirecting clients to HTTPS.";

    // CASE: HTTPS w/valid chain supported and enforced, weak/no HSTS.
    else if ((https == 2) && (behavior >= 2) && (hsts < 2)) {
      if (hsts == 0)
        details = n("Almost:") + " Enable " + l("hsts", "HSTS") + " so that clients can enforce HTTPS.";
      else if (hsts == 1)
        details = n("Almost:") + " The " + l("hsts", "HSTS") + " max-age (" + hsts_age + " seconds) is too short, and should be increased to at least 1 year (31536000 seconds).";
    }

    // CASE: HTTPS supported, not enforced, no HSTS.
    else if ((https >= 1) && (behavior < 2) && (hsts < 2))
      details = "HTTPS supported, but not enforced.";

    // CASE: HTTPS downgrades.
    else if (https == 0)
      details = "Visitors are redirected from HTTPS down to HTTP."

    // CASE: HTTPS isn't supported at all.
    else if (https == -1)
      // TODO SUBCASE: It's a "redirect domain".
      // SUBCASE: Everything else.
      details = "No support for HTTPS."

    else
      details = "";

    return details;
  };

  var loneDomain = function(row) {
    return (row.totals.https.eligible == 1 && row.https.eligible);
  };

  var smartDomain = function(data, type, row) {
    if (type == "sort") return row.domain;

    if (loneDomain(row))
      return Utils.linkDomain(data, type, row);

    return n(row.domain) + " (" + l("#", "" + row.totals.https.eligible + " services") + ")";
  };

  var smartEnforces = function(data, type, row) {
    if (type == "sort") return row.totals.https.enforces;

    if (loneDomain(row))
      return display(names.enforces)(data, type, row);
    else
      return percentBar("https", "enforces")(data, type, row);
  };

  var smartHSTS = function(data, type, row) {
    if (type == "sort") return row.totals.https.hsts;

    if (loneDomain(row))
      return display(names.hsts)(data, type, row);
    else
      return percentBar("https", "hsts")(data, type, row);
  };

  var smartCrypto = function(data, type, row) {
    if (type == "sort") return row.totals.crypto.bod_crypto;

    if (loneDomain(row))
      return display(names.bod_crypto)(data, type, row);
    else
      return percentBar("crypto", "bod_crypto")(data, type, row);
  };

  var initExpansions = function() {
    $('table.domain').on('click', 'tbody tr.odd, tbody tr.even', function() {
      var row = table.row(this);

      if (row.data() == undefined)
        row = table.row(this.previousElementSibling);
      if (row.data() == undefined) return;

      var data = row.data();
      var was_expanded = data.expanded;
      data.expanded = true;
      var base_domain = data.base_domain;

      if (!loneDomain(data) && !was_expanded) {
        console.log("Fetching data for " + base_domain + "...");
        $.ajax({
          url: "/data/hosts/" + base_domain + "/https.json",
          success: function(response) {
            loadSubdomainData(row, base_domain, response);
          },
          error: function() {
            console.log("Error loading data for " + base_domain);
          }
        });
      }

      else if (!loneDomain(data) && was_expanded){
        data.expanded = false;
        row.child.hide();
      }

      return false;
    });
  };

  var renderTable = function(data) {
    table = $("table").DataTable({

      data: data,

      responsive: {
          details: {
              type: "column",
              display: $.fn.dataTable.Responsive.display.childRow
          }
      },

      lengthChange: false,
      pageLength: 100,

      initComplete: function() {
        Utils.searchLinks(this);
        initExpansions(this);
      },

      columns: [
        {
          className: 'control',
          orderable: false,
          data: "",
          render: function() {return ""},
          visible: false
        },
        {
          data: "domain",
          width: "240px",
          cellType: "td",
          render: smartDomain,

          createdCell: function (td) {
            td.scope = "row";
          }
        },
        {data: "agency_name"}, // here for filtering/sorting
        {
          data: "totals.https.enforces",
          render: smartEnforces
        },
        {
          data: "totals.https.hsts",
          render: smartHSTS
        },
        {
          data: "totals.crypto.bod_crypto",
          render: smartCrypto
        },
        {
          data: "https.preloaded",
          render: display(names.preloaded)
        },
        {
          data: "",
          render: showDetails,
        }
      ],

      "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      },

      csv: "/data/domains/https.csv",

      dom: 'pCftrip'

    });

  };

  var links = {
    dap: "https://analytics.usa.gov",
    dap_data: "https://analytics.usa.gov/data/live/sites.csv",
    censys: "https://censys.io",
    hsts: "https://https.cio.gov/hsts/",
    sha1: "https://https.cio.gov/technical-guidelines/#signature-algorithms",
    ssl3: "https://https.cio.gov/technical-guidelines/#ssl-and-tls",
    tls12: "https://https.cio.gov/technical-guidelines/#ssl-and-tls",
    preload: "https://https.cio.gov/hsts/#hsts-preloading",
    subdomains: "/https/guidance/#subdomains",
    preloading_compliance: "https://https.cio.gov/guide/#options-for-hsts-compliance",
    stay_preloaded: "https://hstspreload.org/#continued-requirements",
    submit: "https://hstspreload.org"
  };

  var l = function(slug, text) {
    return "<a href=\"" + (links[slug] || slug) + "\" target=\"blank\">" + text + "</a>";
  };

  var g = function(text) {
    return "<strong class=\"success\">" + text + "</strong>";
  };

  var w = function(text) {
    return "<strong class=\"warning\">" + text + "</strong>";
  };

  var n = function(text) {
    return "<strong class=\"neutral\">" + text + "</strong>";
  }

  // report: e.g. 'https', or 'crypto'
  // field: e.g. 'uses' or 'rc4'
  var percentBar = function(report, field) {
    return function(data, type, row) {
      var percent = Utils.percent(
        row.totals[report][field], row.totals[report].eligible
      );

      if (type == "sort") return percent;
      else return Utils.progressBar(percent);
    };
  };

})
