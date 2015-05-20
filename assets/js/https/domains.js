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
      "-1": "No", // N/A
      0: "No", // Downgrade
      1: "No", // Present, not default
      2: "Yes", // Defaults eventually to HTTPS
      3: "Yes" // Defaults eventually + redirects immediately
    },

    hsts: {
      "-1": "No", // N/A
      0: "No", // No
      1: "Yes", // HSTS on only that domain
      2: "Yes", // HSTS on subdomains
      3: "Yes, and preloaded" // HSTS on subdomains + preload
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

  var renderTable = function(data) {
    $("table").DataTable({

      data: data,

      columns: [
        {data: "Domain"},
        {data: "HTTPS Enabled?"},
        {data: "HTTPS Enforced?"},
        {data: "Strict Transport Security (HSTS)"}
      ],

      columnDefs: [
        {render: display(names.https), targets: 1},
        {render: display(names.https_forced), targets: 2},
        {render: display(names.hsts), targets: 3},
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