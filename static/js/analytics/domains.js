$(document).ready(function () {

  $.get("/static/data/tables/analytics/domains.json", function(data) {
    renderTable(data.data);
  });

  /**
  * I don't like this at all, but to keep the presentation synced
  * between the front-end table, and the CSV we generate, this is
  * getting replicated to the /data/update script in this repository,
  * and needs to be manually synced.
  *
  * The refactor that takes away from DataTables should also prioritize
  * a cleaner way to DRY (don't repeat yourself) this mess up.
  */

  var names = {
    dap: {
      0: "No",
      1: "Yes"
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

      responsive: true,

      data: data,

      initComplete: Utils.searchLinks,

      columns: [
        {
          data: "Domain",
          width: "210px",
          render: Utils.linkDomain
        },
        {data: "Canonical"},
        {data: "Agency"},
        {
          data: "Participates in DAP?",
          render: display(names.dap)
        }
      ],

      columnDefs: [
        {
          targets: 0,
          cellType: "td",
          createdCell: function (td) {
            td.scope = "row";
          }
        }
      ],

      "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      },

      csv: "/static/data/tables/analytics/analytics-domains.csv",

      dom: 'LCftrip'

    });
  };

});
