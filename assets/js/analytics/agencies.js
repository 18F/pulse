$(document).ready(function () {

  $.get("/assets/data/tables/analytics/agencies.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    $("table").DataTable({
      data: data,

      columns: [
        {"data": "Agency"},
        {"data": "Number of Domains"},
        {"data": "Participates in DAP?"}
      ],

      columnDefs: [
        {render: Utils.progressBar, targets: 2}
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
