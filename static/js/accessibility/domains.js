$(document).ready(function () {

  $.get("/static/data/tables/accessibility/domains.json", function(data) {
    renderTable(data.data);
  });

  var detailsKeyboardCtrl = function(){
      $('table tbody tr td:first-child').attr('tabindex','0')
      .attr('aria-label','Select for additional details')
      .on('keydown',function(e){
        if (e.keyCode == 13) {
          // $(this).click();
          // $(this).parent().next('tr.child').focus();
        }
      });
    };

  var renderTable = function(data) {
    var table = $("table").DataTable({

      responsive: true,

      data: data,

      initComplete: Utils.searchLinks,

      columns: [
        {
          data: "domain",
          width: "210px",
          render: Utils.linkDomain
        },
        {
          data: "errors",
          width: "60px",
          },
        {data: "agency"},
        {
          data: "errorlist",
          render: Utils.a11yErrorList
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

      // csv: "/static/data/tables/https/https-domains.csv",

      dom: 'LCftrip'

    });


    /**
    * Make the row expand when any cell in it is clicked.
    *
    * DataTables' child row API doesn't appear to work, likely
    * because we're getting child rows through the Responsive
    * plugin, not directly. We can't put the click event on the
    * whole row, because then sending the click to the first cell
    * will cause a recursive loop and stack overflow.
    *
    * So, we put the click on every cell except the first one, and
    * send it to its sibling. The first cell is already wired.
    */
    $('table tbody').on('click', 'td:not(.sorting_1)', function(e) {
      $(this).siblings("td.sorting_1").click();
    });

    //Adds keyboard control to first cell of table
    detailsKeyboardCtrl();

    table.on("draw.dt",function(){
       detailsKeyboardCtrl();
    });

  };
});
