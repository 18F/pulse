$(document).ready(function () {

  $.get("https://pulse.cio.gov/data/tables/analytics/agencies.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    $("table").DataTable({
      responsive: true,

      data: data,

      initComplete: Utils.searchLinks,

      columns: [
        {data: "Agency"},
        {
          data: "Number of Domains",
          render: Utils.filterAgency("analytics")
        },
        {data: "Participates in DAP?"}
      ],

      // order by number of domains
      order: [[1, "desc"]],

      columnDefs: [
        {
          targets: 0,
          cellType: "td",
          createdCell: function (td) {
            td.scope = "row";
          }
        },
        {
          render: Utils.progressBar,
          targets: 2,
        }
      ],

      "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      },

      dom: 'Lftrip'

    });
  };

});
