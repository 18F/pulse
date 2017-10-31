$(document).ready(function () {

  $.get("/data/agencies/analytics.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    var table = $("table").DataTable({
      responsive: true,

      data: data,

      initComplete: function() {
        Utils.searchLinks(this);
      },

      columns: [
        {
          data: "name",
          cellType: "th"
        },
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
            var percent = Utils.percent(
              row.analytics.participating, row.analytics.eligible
            )
            if (type == "sort")
              return percent;
            return Utils.progressBar(percent);
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

      csv: "/data/hosts/analytics.csv",

      dom: 'LCftrip'

    });

    Utils.updatePagination();
    table.on("draw.dt",function(){
      Utils.updatePagination();
    });
  };

});
