$(document).ready(function () {

  $.get("/static/data/tables/accessibility/agencies.json", function(data) {
    Tables.initAgency(data.data, {
      columns: [
        {
          data: "agency",
          cellType: "th",
          createdCell: function (td) {td.scope = "row";}
        },
        {data: "Color Contrast - Initial Findings"},
        {data: "HTML Attribute - Initial Findings"},
        {data: "Missing Image Descriptions"}
      ]
    });
  });
});
