$(document).ready(function () {

  $.get("/assets/data/tables/https/domains.json", function(data) {
    renderTable(data.data);
  });

  var names = {
    https: {
      0: "No",
      1: "Yes", // (with certificate chain issues)
      2: "Yes"
    },

    https_forced: {
      "-1": "", // N/A
      0: "No", // Downgrade
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

  var renderTable = function(data) {
    $("table").DataTable({

      responsive: true,

      data: data,

      columns: [
        {
          data: "Domain",
          width: "210px",
          render: Utils.linkDomain
        },
        {data: "Canonical"},
        {data: "Agency"},
        {
          data: "HTTPS Enabled?",
          render: display(names.https)
        },
        {
          data: "HTTPS Enforced?",
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
        // {data: "More details"}
      ],

      "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      },

    });
  };

})