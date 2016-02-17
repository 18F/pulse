$(document).ready(function () {

  $.get("/data/agencies/analytics.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    $("table").DataTable({
      responsive: true,

      data: data,

      initComplete: Utils.searchLinks,

      columns: [
        {data: "name"},
        {
          data: "analytics.eligible",
          render: Utils.filterAgency("analytics")
        },
        {
          data: "analytics.participating",
        }
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
          render: function(data, type, row) {
            if (type == "sort")
              return null;
            return Utils.progressBar(Utils.percent(
              row.analytics.participating, row.analytics.eligible
            ));
          },
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
