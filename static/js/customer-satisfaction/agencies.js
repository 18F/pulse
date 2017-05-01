$(document).ready(function () {

  $.get("/static/data/tables/customer-satisfaction/agencies.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    var table = $("table").DataTable({
      responsive: true,

      data: data,

      initComplete: Utils.searchLinks,

      columns: [
        {
          data: "name",
          cellType: "th"
        },
        {
          data: "eligible",
          render: Utils.filterAgency("customer-satisfaction")
        },
        {
          data: "participating",
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
            var percent = Utils.percent(
              row.participating, row.eligible
            )
            if (type == "sort")
              return percent;
            return Utils.progressBar(percent);
          },
          targets: 2,
          type: "html-num-fmt"
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

    Utils.updatePagination();
    table.on("draw.dt",function(){
      Utils.updatePagination();
    });
  };

});
