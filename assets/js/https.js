$(document).ready(function () {

  $.get("/assets/data/tables/https-domains.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    $("table").DataTable({

      data: data,

      columns: [
        {"data":"Domain"},
        {"data":"HTTPS Enabled?"},
        {"data":"HTTPS Enforced?"},
        {"data":"Strict Transport Security (HSTS)"}
      ],

      language: {
        searchPlaceholder: "Start typing..."
      },

    });
  };

})