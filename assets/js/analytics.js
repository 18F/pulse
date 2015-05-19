$(document).ready(function () {

  $.get("/assets/data/tables/analytics-domains.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    $("table").DataTable({
      data: data,

      columns: [
        {"data":"Domain"},
        {"data":"Participates in DAP"}
      ]
    });
  };

});
