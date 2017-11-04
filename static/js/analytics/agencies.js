$(function() {

  $.get("/data/agencies/analytics.json", function(data) {

    Tables.initAgency(data.data, {
      csv: "/data/hosts/analytics.csv",

      columns: [
        {
          data: "name",
          cellType: "th",
          createdCell: function (td) {td.scope = "row";}
        },
        {
          data: "analytics.eligible",
          render: Tables.agencyServices("analytics")
        },
        {
          data: "analytics.participating",
          render: Tables.percent("analytics", "participating")
        }
      ]
    });
  });

});
