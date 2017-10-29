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
      2: "Yes", // Yes, HSTS for >= 1 year (for canonical endpoint)
      3: "Preloaded" // Yes, via preloading (subdomains only)
    },

    bod_crypto: {
      "-1": "--", // No HTTPS
      0: "No",
      1: "Yes"
    },

    // Parent domains only
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

  var displayCrypto = function(row) {
    // if it's all good, then great
    if (row.https.bod_crypto != 0)
      return names.bod_crypto[row.https.bod_crypto];

    var problems = [];
    // if not, what are the problems?
    if (row.https.rc4) problems.push("RC4");
    if (row.https['3des']) problems.push("3DES");
    if (row.https.sslv2) problems.push("SSLv2");
    if (row.https.sslv3) problems.push("SSLv3");

    return "No, uses " + problems.join(", ");
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

      var crypto = displayCrypto(subdomain);
      details.append($("<td/>").html(crypto));

      // blank
      details.append($("<td/>"));

      all.push(details);
    }

    row.child(all, "child").show();
  };

  var loneDomain = function(row) {
    return (row.is_parent && row.totals.https.eligible == 1 && row.https.eligible);
  };

  var showDomain = function(data, type, row) {
    if (type == "sort") return row.domain;

    if (loneDomain(row))
      return Utils.linkDomain(data, type, row);

    return n(row.domain) + " (" + l("#", "show " + row.totals.https.eligible + " services") + ")";
  };

  var showEnforces = function(data, type, row) {
    if (type == "sort") return row.totals.https.enforces;

    if (loneDomain(row))
      return names.enforces[row.https.enforces];
    else
      return percentBar("https", "enforces")(data, type, row);
  };

  var showHSTS = function(data, type, row) {
    if (type == "sort") return row.totals.https.hsts;

    if (loneDomain(row))
      return names.hsts[row.https.hsts];
    else
      return percentBar("https", "hsts")(data, type, row);
  };

  var showCrypto = function(data, type, row) {
    if (type == "sort") return row.totals.crypto.bod_crypto;

    if (loneDomain(row))
      return displayCrypto(row);
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
          render: showDomain,

          createdCell: function (td) {
            td.scope = "row";
          }
        },
        {data: "agency_name"}, // here for filtering/sorting
        {
          data: "totals.https.enforces",
          render: showEnforces
        },
        {
          data: "totals.https.hsts",
          render: showHSTS
        },
        {
          data: "totals.crypto.bod_crypto",
          render: showCrypto
        },
        {
          data: "https.preloaded",
          render: display(names.preloaded)
        },
        {
          data: "",
          render: function() {return "";},
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
      var eligible = row.totals[report].eligible;
      if (eligible == 0) {
        if (type == "sort") return 100; // shrug
        else return "--";
      }
      else {
        var percent = Utils.percent(row.totals[report][field], eligible);
        if (type == "sort") return percent;
        else return Utils.progressBar(percent);
      }
    };
  };

})
