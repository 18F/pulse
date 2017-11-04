$(function() {

  $.get("/static/data/tables/customer-satisfaction/domains.json", function(data) {
    var table = Tables.init(data.data, {

      columns: [
        {
          data: "domain",
          width: "210px",
          cellType: "th",
          createdCell: function (td) {td.scope = "row"}
        },
        {data: "canonical"},
        {data: "agency_name"},
        {
          data: "participating",
          render: Tables.boolean
        },
        {
          data:"service-list",
          render: custSatList
        }
      ]

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
      $(this).siblings("th.sorting_1").click();
    });

    // TODO: move this to Tables.js.
    // Adds keyboard control to first cell of table
    Utils.detailsKeyboardCtrl();
    table.on("draw.dt",function(){
       Utils.detailsKeyboardCtrl();
    });
  });

  var custSatList = function(data, type, row) {
    var custSatListOutput = "";

    $.each(data, function(key, value) {
      if (value)
        custSatListOutput += "<li><a href=\"" + value + "\">" + key + "</a></li>";
    });

    if (!custSatListOutput)
      return "<span class=\"noErrors\">No customer satisfaction tools used.</span>";
    else
      return "<ul class=\"errorList\">" + custSatListOutput + "</ul></hr>";
  };

});
