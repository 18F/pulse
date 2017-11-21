$(function () {

  $.get("/data/hosts/analytics.json", function(data) {
    var table = Tables.init(data.data, {

      csv: "/data/hosts/analytics.csv",

      columns: [
        {
          data: "domain",
          width: "210px",
          cellType: "th",
          render: Tables.canonical
        },
        {data: "canonical"},
        {data: "agency_name"},
        {
          data: "analytics.participating",
          render: Tables.boolean
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
      ]
    });
  });

});
