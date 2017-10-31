$(document).ready(function () {

  $.get("/static/data/tables/accessibility/agencies.json", function(data) {
    renderTable(data.data);
  });

  var renderTable = function(data) {
    var table = $("table").DataTable({
      responsive: true,

      initComplete: function() {
        Utils.searchLinks(this);
      },

      data: data,

      columns: [
        {
          data: "agency",
          cellType: "th"
        },
        {
          data: "Color Contrast - Initial Findings"
        },
        {
          data: "HTML Attribute - Initial Findings"
        },
        {
          data: "Missing Image Descriptions"
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
