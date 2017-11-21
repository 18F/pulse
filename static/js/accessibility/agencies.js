$(document).ready(function () {

  // break caching
  var time = (new Date()).getTime();

  $.get("/static/data/tables/accessibility/agencies.json?" + time, function(data) {
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
