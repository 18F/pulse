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
      0: "No",
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
      0: "No", // No
      1: "Yes", // HSTS on only that domain
      2: "Yes", // HSTS on subdomains
      3: "Yes, and preload-ready", // HSTS on subdomains + preload flag
      4: "Yes, and preloaded" // In the HSTS preload list
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
        return data;
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
        "<a href=\"" + labsUrlFor(row.domain) + "\" target=\"blank\">" +
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

    var details;

    if (https >= 1) {
      if (behavior >= 2)
        details = "This domain enforces HTTPS. "
      else
        details = "This domain supports HTTPS, but does not enforce it. "

      if (hsts == 0) {
        // HSTS is considered a No *because* its max-age is too weak.
        if ((hsts_age > 0) && (hsts_age < 10886400))
          details += "The " + l("hsts", "HSTS") + " max-age (" + hsts_age + " seconds) is too short, and should be increased to at least 1 year (31536000 seconds).";
        else
          details += l("hsts", "HSTS") + " is not enabled.";
      }
      else if (hsts == 1)
        details += l("hsts", "HSTS") + " is enabled, but not for its subdomains and is not ready for " + l("preload", "preloading") + ".";
      else if (hsts == 2)
        details += l("hsts", "HSTS") + " is enabled for all subdomains, but is not ready for " + l("preload", "preloading into browsers") + ".";
      else if (hsts == 3)
        details += l("hsts", "HSTS") + " is enabled for all subdomains, and can be " + l("preload", "preloaded into browsers") + ".";

      // HSTS is strong enough to get a yes, but still less than a year.
      if (hsts > 0 && (hsts_age < 31536000))
        details += " The HSTS max-age (" + hsts_age + " seconds) should be increased to at least 1 year (31536000 seconds)."

    } else if (https == 0)
      details = "This domain redirects visitors from HTTPS down to HTTP."
    else if (https == -1)
      details = "This domain does not support HTTPS."

    return details;
  };

  var links = {
    rc4: "https://https.cio.gov/technical-guidelines/#rc4",
    hsts: "https://https.cio.gov/hsts/",
    sha1: "https://https.cio.gov/technical-guidelines/#signature-algorithms",
    ssl3: "https://https.cio.gov/technical-guidelines/#ssl-and-tls",
    tls: "https://https.cio.gov/technical-guidelines/#ssl-and-tls",
    fs: "https://https.cio.gov/technical-guidelines/#forward-secrecy",
    preload: "https://https.cio.gov/hsts/#hsts-preloading"
  };

  var l = function(slug, text) {
    return "<a href=\"" + (links[slug] || slug) + "\" target=\"blank\">" + text + "</a>";
  };

  // Mention a few high-impact TLS issues that will have affected
  // the SSL Labs grade.
  var tlsDetails = function(data, type, row) {
    if (type == "sort")
      return null;

    if (row.https.grade < 0)
      return "No data.";

    var config = [];

    if (row.https.uses == 1)
      config.push("uses a certificate chain that may be invalid for some visitors");

    if (row.https.sig == "SHA1withRSA")
      config.push("uses a certificate with a " + l("sha1", "weak SHA-1 signature"));

    if (row.https.ssl3 == true)
      config.push("supports the " + l("ssl3", "insecure SSLv3 protocol"));

    if (row.https.rc4 == true)
      config.push("supports the " + l("rc4", "deprecated RC4 cipher"));

    if (row.https.tls12 == false)
      config.push("lacks support for the " + l("tls", "most recent version of TLS"));

    // Don't bother remarking if FS is Modern or Robust.
    if (row.https.fs <= 1)
      config.push("should enable " + l("fs", "forward secrecy"));

    var issues = "";
    if (config.length > 0)
      issues += "This domain " + config.join(", ") + ". ";

    issues += "See the " + l(labsUrlFor(row.domain), "full SSL Labs report") + " for details.";

    return issues;
  };

  var detailsKeyboardCtrl = function(){
      $('table tbody tr td:first-child').attr('tabindex','0')
      .attr('aria-label','Select for additional details')
      .on('keydown',function(e){
        if (e.keyCode == 13)
          $(this).click();
          $(this).parent().next('tr.child').focus();
      })
    };

  var renderTable = function(data) {
    var table = $("table").DataTable({

      responsive: true,

      data: data,

      initComplete: Utils.searchLinks,

      columns: [
        {
          data: "domain",
          width: "210px",
          cellType: "th",
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
          data: "https.grade",
          render: linkGrade
        },
        {
          data: "Details",
          render: httpDetails
        },
        {
          data: "TLS Issues",
          render: tlsDetails
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


    /**
    * Make the row expand when any cell in it is clicked.
    *
    * DataTables' child row API doesn't appear to work, likely
    * because we're getting child rows through the Responsive
    * plugin, not directly. We can't put the click event on the
    * whole row, because then sending the click to the first cell
    * will cause a recursive loop and stack overflow.
    *
    * So, we put the click on every cell except the first one, and
    * send it to its sibling. The first cell is already wired.
    */
    $('table tbody').on('click', 'td:not(.sorting_1)', function(e) {
      $(this).siblings("th.sorting_1").click();
    });


    //Adds keyboard control to first cell of table
    detailsKeyboardCtrl();

    table.on("draw.dt",function(){
       detailsKeyboardCtrl();
    });

  }

})
