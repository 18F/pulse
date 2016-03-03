$(document).ready(function () {

  $.get("/static/data/tables/accessibility/domains.json", function(data) {
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
    https: {
      "-1": "No",
      0: "No",
      1: "Yes", // (with certificate chain issues)
      2: "Yes"
    },

    https_forced: {
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
    return function(data, type) {
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
        "<a href=\"" + labsUrlFor(row['Domain']) + "\" target=\"blank\">" +
          grade +
        "</a>";
  };

  var labsUrlFor = function(domain) {
    return "https://www.ssllabs.com/ssltest/analyze.html?d=" + domain;
  };


  // Construct a sentence explaining the HTTP situation.
  var accessibilityDetails = function(data, type, row) {
    var errors= ["Duplicate id attribute value \"\" found on the web page. *this is not real data", "This element has insufficient contrast at this conformance level. Expected a contrast ratio of at least 4.5:1, but text in this element has a contrast ratio of 3.4:1. Recommendation: change text colour to #636363. *this is not real data"];
    var error_string = '';
    for (var i=0; i<errors.length; i++){
      error_string += "<hr/><li>" + errors[i] + "</li>";
    }
    return "<ol>" + error_string + "</ol>";
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

    if (row["SSL Labs Grade"] < 0)
      return "No data.";

    var config = [];

    if (row["Uses HTTPS"] == 1)
      config.push("uses a certificate chain that may be invalid for some visitors");

    if (row["Signature Algorithm"] == "SHA1withRSA")
      config.push("uses a certificate with a " + l("sha1", "weak SHA-1 signature"));

    if (row["SSLv3"] == true)
      config.push("supports the " + l("ssl3", "insecure SSLv3 protocol"));

    if (row["RC4"] == true)
      config.push("supports the " + l("rc4", "deprecated RC4 cipher"));

    if (row["TLSv1.2"] == false)
      config.push("lacks support for the " + l("tls", "most recent version of TLS"));

    // Don't bother remarking if FS is Modern or Robust.
    if (row["Forward Secrecy"] <= 1)
      config.push("should enable " + l("fs", "forward secrecy"));

    var issues = "";
    if (config.length > 0)
      issues += "This domain " + config.join(", ") + ". ";

    issues += "See the " + l(labsUrlFor(row["Domain"]), "full SSL Labs report") + " for details.";

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
          data: "Domain",
          width: "210px",
          render: Utils.linkDomain
        },
        {data: "Errors"},
        {data: "Agency"},
        {
          data: "Error Details",
          render: accessibilityDetails
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

      csv: "/static/data/tables/https/https-domains.csv",

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
      $(this).siblings("td.sorting_1").click();
    });


    //Adds keyboard control to first cell of table
    detailsKeyboardCtrl();

    table.on("draw.dt",function(){
       detailsKeyboardCtrl();
    });

  }

})