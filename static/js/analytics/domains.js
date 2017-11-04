$(document).ready(function () {

  $.get("/data/domains/analytics.json", function(data) {
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
      false: "No",
      true: "Yes"
    }
  };



  var display = function(set) {
    return function(data, type) {
      if (type == "sort")
        return set[data];
      else
        return set[data];
    }
  };

  var renderTable = function(data) {
    var table = $("table").DataTable({

      responsive: true,

      data: data,

      initComplete: function() {
        Utils.searchLinks(this);
      },

      columns: [
        {
          data: "domain",
          width: "210px",
          cellType: "th",
          render: Utils.linkDomain
        },
        {data: "canonical"},
        {data: "agency_name"},
        {
          data: "analytics.participating",
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

      csv: "/data/hosts/analytics.csv",

      dom: 'LCftrip'

    });

    Utils.updatePagination();
    table.on("draw.dt",function(){
      Utils.updatePagination();
    });
  };

});
