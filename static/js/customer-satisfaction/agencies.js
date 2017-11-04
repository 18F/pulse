$(function () {

  $.get("/static/data/tables/customer-satisfaction/agencies.json", function(data) {
    Tables.initAgency(data.data, {

      columns: [
        {
          data: "name",
          cellType: "th",
          createdCell: function (td) {td.scope = "row";}
        },
        {
          data: "eligible",
          render: Tables.agencyServices("customer-satisfaction")
        },
        {
          data: "participating",
          type: "html-num-fmt",

          // TODO: Use Tables.percent once the participating/eligible
          // fields are nested under an underlying report, like the others.
          render: function(data, type, row) {
            var percent = Utils.percent(row.participating, row.eligible);
            if (type == "sort") return percent;
            return Tables.percentBar(percent);
          }
        }
      ]
    });
  });
});
