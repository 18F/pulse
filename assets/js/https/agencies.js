$(document).ready(function () {

  $.get("/assets/data/tables/https/agencies.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    $("table").DataTable({
      data: data,

      columns: [
        {data: "Agency"},
        {data: "Number of Domains"},
        {data: "HTTPS Enabled?"},
        {data: "HTTPS Enforced?"},
        {data: "Strict Transport Security (HSTS)"}
      ],

      columnDefs: [
        {render: Utils.progressBar, targets: 2},
        {render: Utils.progressBar, targets: 3},
        {render: Utils.progressBar, targets: 4}
      ],

      "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      }

    });
  };

});
