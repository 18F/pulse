$(function () {

  // referenced in a few places
  var table;

  // Populate with parent domain data, expand hosts per-domain
  $.get("/data/domains/https.json", function(data) {
    table = Tables.init(data.data, {

      csv: "/data/hosts/https.csv",

      responsive: {
          details: {
              type: "column",
              display: $.fn.dataTable.Responsive.display.childRow
          }
      },

      initComplete: initExpansions,

      columns: [
        {
          className: 'control',
          orderable: false,
          data: "",
          render: Tables.noop,
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
          data: "totals.https.compliant",
          render: Tables.percentTotals("https", "compliant"),
          width: "100px",
          className: "compliant"
        },
        {
          data: "totals.https.enforces",
          render: Tables.percentTotals("https", "enforces")
        },
        {
          data: "totals.https.hsts",
          render: Tables.percentTotals("https", "enforces")
        },
        {
          data: "totals.crypto.bod_crypto",
          render: Tables.percentTotals("crypto", "bod_crypto")
        },
        {
          data: "https.preloaded",
          render: display(names.preloaded)
        },
        {
          data: "",
          render: Tables.noop
        }
      ]
    });
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
    },

    compliant: {
      false: "No",
      true: "Yes"
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

  var loadHostData = function(tr, base_domain, hosts) {
    var all = [];
    var number = hosts.length;

    if (number > 1) {
      var csv = "/data/hosts/" + base_domain + "/https.csv";
      var discoveryLink = l("/https/guidance/#subdomains", "publicly discoverable services");
      var link = "Showing data for " + number + " " + discoveryLink + " within " + base_domain + ".&nbsp;&nbsp;";
      link += l(csv, "Download all " + base_domain + " data as a CSV") + ".";
      var download = $("<tr></tr>").addClass("subdomain").html("<td class=\"link\" colspan=6>" + link + "</td>");
      all.push(download);
    }

    for (i=0; i<hosts.length; i++) {
      var host = hosts[i];
      var details = $("<tr/>").addClass("host");

      var link = "<a href=\"" + host.canonical + "\" target=\"blank\">" + Utils.truncate(host.domain, 35) + "</a>";
      details.append($("<td/>").addClass("link").html(link));

      var compliant = names.compliant[host.https.compliant];
      details.append($("<td class=\"compliant\"/>").html(compliant));

      var https = names.enforces[host.https.enforces];
      details.append($("<td/>").html(https));

      var hsts = names.hsts[host.https.hsts];
      details.append($("<td/>").html(hsts));

      var crypto = displayCrypto(host);
      details.append($("<td/>").html(crypto));

      // blank
      details.append($("<td/>"));

      all.push(details);
    }

    tr.child(all, "child");
  };

  var loneDomain = function(row) {
    return (row.is_parent && row.totals.https.eligible == 1 && row.https.eligible);
  };

  var showDomain = function(data, type, row) {
    if (type == "sort") return row.domain;

    // determines whether remote fetching has to happen
    var fetch = !(loneDomain(row));

    return n(row.domain) + " (" + l("#", showHideText(true, row), "onclick=\"return false\" data-fetch=\"" + fetch + "\" data-domain=\"" + row.domain + "\"") + ")";
  };

  var showHideText = function(show, row) {
    if (loneDomain(row))
      return (show ? "show" : "hide") + " details";
    else
      return (show ? "show" : "hide") + " " + row.totals.https.eligible + " services";
  };

  var initExpansions = function() {
    $('table.domain').on('click', 'tbody tr.odd, tbody tr.even', function() {
      var row = table.row(this);

      // zero in on the parent row, whichever was clicked
      if (row.data() == undefined)
        row = table.row(this.previousElementSibling);
      if (row.data() == undefined) return;

      var data = row.data();
      var was_expanded = data.expanded;
      var base_domain = data.base_domain;

      if (!was_expanded) {
        data.expanded = true;

        // link's data-fetch will tell us whether data has to be fetched
        var link = $("a[data-domain='" + base_domain + "']");
        var fetch = link.data("fetch");

        if (fetch) {
          console.log("Fetching data for " + base_domain + "...");
          link.addClass("loading").html("Loading " + base_domain + " services...");

          $.ajax({
            url: "/data/hosts/" + base_domain + "/https.json",
            success: function(response) {
              loadHostData(row, base_domain, response.data);

              // show the data right away
              row.child.show()

              // set it to just show/hide from now on without fetching
              link.data("fetch", false);

              // disable loading styles
              link.removeClass("loading");

              // show the "hide" text
              link.html(showHideText(false, data));
            },
            error: function() {
              console.log("Error loading data for " + base_domain);
            }
          });
        } else {
          // if it's a lone domain, just refill the data every time
          // instead of making this function's logic even more elaborate
          if (loneDomain(data))
            loadHostData(row, base_domain, [data]);

          // show the "hide" text
          link.html(showHideText(false, data));

          row.child.show();
        }

      }

      else { // was_expanded == true
        data.expanded = false;
        row.child.hide();
        $("a[data-domain='" + base_domain + "']").html(showHideText(true, data));
      }

      return false;
    });
  };

  var l = function(href, text, extra) {
    return "<a href=\"" + href + "\" target=\"blank\" " + extra + ">" + text + "</a>";
  };

  var n = function(text) {
    return "<strong class=\"neutral\">" + text + "</strong>";
  }

})
