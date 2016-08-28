$(document).ready(function () {

  $.get("/static/data/tables/accessibility/agencies.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    var table = $("table").DataTable({
      responsive: true,
      initComplete: Utils.searchLinks,

      data: data,

      columns: [
        {
          data: "Agency",
          cellType: "th"
        },
        {
          data: function(row, type, val, meta) {
            return Math.round(row["Average Errors per Page"]);
          },
          width: "76px"
        },
        {
          data: "Color Contrast Errors",
          width: "76px"
        },
        {
          data: "HTML/Attribute Errors"
        },
        {
          data: "Form Errors"
        },
        {
          data: "Alt Tag Errors"
        },
        {
          data: "Other Errors"
        }
      ],

      order: [[1, "desc"]],

      columnDefs: [
        {
          targets: 0,
          cellType: "th",
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

      dom: 'Lftrip'

    });

    Utils.updatePagination();
    table.on("draw.dt",function(){
      Utils.updatePagination();
    });
  };
  
});
