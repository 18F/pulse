$(document).ready(function () {

  $.get("/assets/data/tables/https/domains.json", function(data) {
    renderTable(data.data);
  });

  var names = {
    https: {
      "-1": "No",
      0: "No",
      1: "Yes*", // (with certificate chain issues)
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
      3: "Yes, and preloaded" // HSTS on subdomains + preload
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
    },

    // Straight from SSL Labs API docs: https://github.com/ssllabs/ssllabs-scan/blob/stable/ssllabs-api-docs.md#endpointdetails
    fs: {
      0: "No",
      1: "Some",
      2: "Modern",
      4: "Robust"
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
  var httpDetails = function(data, type, row) {
    if (type == "sort")
      return null;

    var https = row["Uses HTTPS"];
    var behavior = row["Enforces HTTPS"];
    var hsts = row["Strict Transport Security (HSTS)"];

    var details;

    if (https >= 1) {
      if (behavior >= 2)
        details = "This domain enforces HTTPS."
      else
        details = "This domain supports HTTPS, but does not enforce it."

      if (https == 1)
        details += " However, it uses a certificate chain that may cause issues for some visitors."
    } else if (https == 0)
      details = "This domain redirects visitors from HTTPS down to HTTP."
    else if (https == -1)
      details = "This domain does not support HTTPS."

    return details;
  };

  var links = {
    rc4: "https://tools.ietf.org/html/rfc7465",
    hsts: "https://https.cio.gov/hsts/",
    sha1: "http://googleonlinesecurity.blogspot.com/2014/09/gradually-sunsetting-sha-1.html",
    ssl3: "https://www.openssl.org/~bodo/ssl-poodle.pdf",
    fs: "https://blog.twitter.com/2013/forward-secrecy-at-twitter"
  };

  var l = function(slug, text) {
    return "<a href=\"" + links[slug] + "\" target=\"blank\">" + text + "</a>";
  };

  // Mention a few high-impact TLS issues that will have affected
  // the SSL Labs grade.
  var tlsDetails = function(data, type, row) {
    if (type == "sort")
      return null;

    if (row["SSL Labs Grade"] < 0)
      return "";

    var config = [];

    if (row["Signature Algorithm"] == "SHA1withRSA")
      config.push("uses a certificate with a " + l("sha1", "weak SHA-1 signature"));

    if (row["SSLv3"] == true)
      config.push("supports the " + l("ssl3", "insecure SSLv3 protocol"));

    if (row["RC4"] == true)
      config.push("supports the " + l("rc4", "deprecated RC4 cipher"));

    if (row["TLSv1.2"] == false)
      config.push("lacks support for the most recent version of TLS");

    // Don't bother remarking if FS is Modern or Robust.
    if (row["Forward Secrecy"] <= 1)
      config.push("should enable " + l("fs", "forward secrecy"));

    if (config.length > 0)
      return "This domain " + config.join(", ") + ". ";
    else
      return "";
  };

  var renderTable = function(data) {
    $("table").DataTable({

      responsive: true,

      data: data,

      initComplete: Utils.searchLinks,

      columns: [
        {
          data: "Domain",
          width: "210px",
          render: Utils.linkDomain
        },
        {data: "Canonical"},
        {data: "Agency"},
        {
          data: "Uses HTTPS",
          render: display(names.https)
        },
        {
          data: "Enforces HTTPS",
          render: display(names.https_forced)
        },
        {
          data: "Strict Transport Security (HSTS)",
          render: display(names.hsts)
        },
        {
          data: "SSL Labs Grade",
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

      "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      }

    });


  }

})