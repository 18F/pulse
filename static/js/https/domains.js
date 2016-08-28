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
    },

    grade: {
      "-1": "",
      0: "F",
      1: "T",
      2: "C",
      3: "B",
      4: "A-",
      5: "A",
      6: "A+"
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

  var linkGrade = function(data, type, row) {
    var grade = display(names.grade)(data, type);
    if (type == "sort")
      return grade;
    else if (grade == "")
      return ""
    else
      return "" +
        "<a href=\"" + labsUrlFor(row.canonical) + "\" target=\"blank\">" +
          grade +
        "</a>";
  };

  var labsUrlFor = function(domain) {
    return "https://www.ssllabs.com/ssltest/analyze.html?d=" + domain;
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
    var grade = row.https.grade;

    var tls = [];

    // If an SSL Labs grade exists at all...
    if (row.https.grade >= 0) {

      if (row.https.sig == "SHA1withRSA")
        tls.push("Certificate uses a " + l("sha1", "weak SHA-1 signature"));

      if (row.https.ssl3 == true)
        tls.push("Supports the " + l("ssl3", "insecure SSLv3 protocol"));

      if (row.https.tls12 == false)
        tls.push("Lacks support for the " + l("tls12", "most recent version of TLS"));
    }

    // Though not found through SSL Labs, this is a TLS issue.
    if (https == 1)
      tls.push("Certificate chain not valid for all public clients. See " + l(labsUrlFor(row.canonical), "SSL Labs") + " for details.");

    // Non-urgent TLS details.
    var tlsDetails = "";
    if (grade >= 0) {
      if (tls.length > 0)
        tlsDetails += tls.join(". ") + ".";
      else if (grade < 6)
        tlsDetails += l(labsUrlFor(row.canonical), "Review SSL Labs report") + " to resolve TLS quality issues.";
    }

    // Principles of message crafting:
    //
    // * Only grant "perfect score!" if TLS quality issues are gone.
    // * Don't show TLS quality issues when pushing to preload.
    // * All flagged TLS quality issues should be reflected in the
    //   SSL Labs grade, so that agencies have fair warning of issues
    //   even before we show them.
    // * Don't speak explicitly about M-15-13, since not all domains
    //   are subject to OMB requirements.

    var details;
    // By default, if it's an F grade, *always* give TLS details.
    var urgent = (grade == 0);

    // CASE: Perfect score!
    if (
        (https >= 1) && (behavior >= 2) &&
        (hsts == 2) && (preloaded == 2) &&
        (tls.length == 0) && (grade == 6))
      details = g("Perfect score! HTTPS is strictly enforced throughout the zone.");

    // CASE: Only issue is TLS quality issues.
    else if (
        (https >= 1) && (behavior >= 2) &&
        (hsts == 2) && (preloaded == 2)) {
      details = g("Almost perfect!") + " " + tlsDetails;
      // Override F grade override.
      urgent = false;
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
      details = n("Almost:") + " Domain is missing " + l("hsts", "HSTS") + ", but the presented certificate chain may not be valid for all public clients. HSTS prevents users from clicking through certificate warnings. See " + l(labsUrlFor(row.canonical), "the SSL Labs report") + " for details.";

    // CASE: HTTPS supported, not enforced, no HSTS.
    else if ((https >= 1) && (behavior < 2) && (hsts < 2))
      details = "HTTPS supported, but not enforced.";

    // CASE: HTTPS downgrades.
    else if (https == 0)
      details = "HTTPS redirects visitors down to HTTP."

    // CASE: HTTPS isn't supported at all.
    else if (https == -1)
      // TODO SUBCASE: It's a "redirect domain".
      // SUBCASE: Everything else.
      details = "No support for HTTPS."

    else
      details = "";

    // If there's an F grade, and TLS details weren't already included,
    // add an urgent warning.
    if (urgent)
      return details + " " + w("Warning: ") + l(labsUrlFor(row.canonical), "review SSL Labs report") + " to resolve TLS quality issues."
    else
      return details;
  };

  var links = {
    hsts: "https://https.cio.gov/hsts/",
    sha1: "https://https.cio.gov/technical-guidelines/#signature-algorithms",
    ssl3: "https://https.cio.gov/technical-guidelines/#ssl-and-tls",
    tls12: "https://https.cio.gov/technical-guidelines/#ssl-and-tls",
    preload: "https://https.cio.gov/hsts/#hsts-preloading",
    stay_preloaded: "https://hstspreload.appspot.com/#continued-requirements",
    submit: "https://hstspreload.appspot.com"
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
          render: Utils.linkDomain
        },
        {data: "canonical"},
        {data: "agency_name"},
        {
          data: "https.uses",
          render: display(names.uses)
        },
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
        },
        {
          data: "https.grade",
          render: linkGrade
        },
        {
          data: "",
          render: httpDetails
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
