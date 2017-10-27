$(document).ready(function () {

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
    uses: {
      "-1": "No",
      0: "No",  // Downgrades HTTPS -> HTTP
      1: "Yes", // (with certificate chain issues)
      2: "Yes"
    },

    enforces: {
      0: "", // N/A (no HTTPS)
      1: "No", // Present, not default
      2: "Yes", // Defaults eventually to HTTPS
      3: "Yes" // Defaults eventually + redirects immediately
    },

    hsts: {
      "-1": "", // N/A
      0: "No",  // No
      1: "No", // No, HSTS with short max-age (for canonical endpoint)
      2: "Yes" // Yes, HSTS for >= 1 year (for canonical endpoint)
    },

    preloaded: {
      0: "",  // No (don't display, since it's optional)
      1: "Ready",  // Preload-ready
      2: "Yes"  // Yes
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

  // Describe what's going on with this domain's subdomains.
  var subdomains = function(data, type, row) {
    if (type == "sort") return null;

    // If the domain is preloaded, responsibilities are absolved.
    if (row.https.preloaded == 2)
      return "All subdomains automatically protected through preloading.";

    if (row.https.preloaded == 1)
      return "All subdomains will be protected when preloading is complete.";

    if (!row.https.subdomains) {
      if (row.https.uses >= 1)
        return "No public subdomains found. " + l("preload", "Consider preloading.");
      else
        return "No public subdomains found.";
    }

    var sources = [],
        message = "",
        pct = null;

    // TODO: make this a function.
    if (row.https.subdomains.censys) {
      pct = Utils.percent(row.https.subdomains.censys.enforces, row.https.subdomains.censys.eligible);
      message = n("" + pct + "%") + " of " +
        row.https.subdomains.censys.eligible + " public sites "
        + "known to Censys" +
        " enforce HTTPS.";
      sources.push(message);
    }

    if (row.https.subdomains.dap) {
      pct = Utils.percent(row.https.subdomains.dap.enforces, row.https.subdomains.dap.eligible);
      sources.push(n("" + pct + "%") + " of " +
        row.https.subdomains.dap.eligible + " public sites " +
        "known to the Digital Analytics Program" +
        " enforce HTTPS.")
    }

    if (sources.length == 0)
      return "";

    sources.push("For more details, " + l(links.subdomains, "read our methodology") +
      ", or " + l(agencyDownloadFor(row), "download subdomain data for this agency") + ".");

    var p = "<p class=\"indents\">";
    return n("Known public subdomains: ") + p + sources.join("</p>" + p) + "</p>";
  };

  var agencyDownloadFor = function(row) {
    return "https://s3-us-gov-west-1.amazonaws.com/cg-4adefb86-dadb-4ecf-be3e-f1c7b4f6d084/live/subdomains/agencies/" + row["agency_slug"] + "/https.csv";
  };

  // Construct a sentence explaining the HTTP situation.
  var httpDetails = function(data, type, row) {

    if (type == "sort")
      return null;

    var https = row.https.uses;
    var behavior = row.https.enforces;
    var hsts = row.https.hsts;
    var hsts_age = row.https.hsts_age;
    var preloaded = row.https.preloaded;
    var crypto = row.https.bod_crypto;

    var details;

    // CASE: Perfect score!
    // HSTS max-age is allowed to be weak, because client enforcement means that
    // the max-age is effectively overridden in modern browsers.
    if (
        (https >= 1) && (behavior >= 2) &&
        (hsts == 2) && (preloaded == 2)) {
      details = g("Perfect score! HTTPS is strictly enforced throughout the zone.");
    }

    // CASE: HSTS preloaded, but HSTS header is missing.
    else if (
        (https >= 1) && (behavior >= 2) &&
        (hsts < 1) && (preloaded == 2))
      details = n("Caution:") + " Domain is preloaded, but HSTS header is missing. This may " + l("stay_preloaded", "cause the domain to be un-preloaded") + ".";

    // CASE: HTTPS+HSTS, preload-ready but not preloaded.
    else if (
        (https >= 1) && (behavior >= 2) &&
        (hsts == 2) && (preloaded == 1))
      details = g("Almost there! ") + "Domain is ready to be " + l("submit", "submitted to the HSTS preload list") + ".";

    // CASE: HTTPS+HSTS (M-15-13 compliant), but no preloading.
    else if (
        (https >= 1) && (behavior >= 2) &&
        (hsts == 2) && (preloaded == 0))
      details = g("HTTPS enforced. ") + n(l("preload", "Consider preloading this domain")) + " to enforce HTTPS across the entire zone.";

    // CASE: HSTS, but HTTPS not enforced.
    else if ((https >= 1) && (behavior < 2) && (hsts == 2))
      details = n("Caution:") + " Domain uses " + l("hsts", "HSTS") + ", but is not redirecting clients to HTTPS.";

    // CASE: HTTPS w/valid chain supported and enforced, weak/no HSTS.
    else if ((https == 2) && (behavior >= 2) && (hsts < 2)) {
      if (hsts == 0)
        details = n("Almost:") + " Enable " + l("hsts", "HSTS") + " so that clients can enforce HTTPS.";
      else if (hsts == 1)
        details = n("Almost:") + " The " + l("hsts", "HSTS") + " max-age (" + hsts_age + " seconds) is too short, and should be increased to at least 1 year (31536000 seconds).";
    }

    // CASE: HTTPS w/invalid chain supported and enforced, no HSTS.
    else if ((https == 1) && (behavior >= 2) && (hsts < 2))
      details = n("Almost:") + " Domain is missing " + l("hsts", "HSTS") + ", but the presented certificate chain may not be valid for all public clients. HSTS prevents users from clicking through certificate warnings.";

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

  var renderTable = function(data) {
    var table = $("table").DataTable({

      data: data,

      responsive: {
          details: {
              type: "",
              display: $.fn.dataTable.Responsive.display.childRowImmediate
          }
      },

      initComplete: Utils.searchLinks,

      columns: [
        {
          data: "domain",
          width: "210px",
          cellType: "th",
          render: Utils.linkDomain
        },
        {data: "canonical"}, // why is this here?
        {data: "agency_name"}, // here for filtering/sorting
        {
          data: "https.enforces",
          render: display(names.enforces)
        },
        {
          data: "https.hsts",
          render: display(names.hsts)
        },
        {
          data: "https.preloaded",
          render: display(names.preloaded)
        }
      ],

      columnDefs: [
        {
          targets: 0,
          cellType: "td",
          createdCell: function (td) {
            td.scope = "row";
          }
        }
      ],

      "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      },

      csv: "/data/domains/https.csv",

      dom: 'LCftrip'

    });

  }

})
