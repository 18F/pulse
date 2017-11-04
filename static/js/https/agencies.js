$(document).ready(function () {

  $.get("/data/agencies/https.json", function(data) {
    Tables.initAgency(data.data, {

      csv: "/data/hosts/https.csv",

      columns: [
        {
          cellType: "th",
          createdCell: function (td) {td.scope = "row";},
          data: "name"
        },
        {
          data: "https.eligible", // sort on this, but
          render: eligibleHttps,
          type: "num"
        },
        {
          data: "https.compliant",
          render: Tables.percent("https", "enforces"),
          className: "compliant",
          width: "100px"
        },
        {
          data: "https.enforces",
          render: Tables.percent("https", "enforces")
        },
        {
          data: "https.hsts",
          render: Tables.percent("https", "hsts")
        },
        {
          data: "crypto.bod_crypto",
          render: Tables.percent("crypto", "bod_crypto")
        },
        {
          data: "preloading.preloaded",
          render: Tables.percent("preloading", "preloaded")
        }
      ]

    });
  });

  var eligibleHttps = function(data, type, row) {
    var services = row.https.eligible;
    var domains = row.total_domains;
    if (type == "sort") return services;

    var link = function(text) {
      return "" +
        "<a href=\"/https/domains/#" +
          QueryString.stringify({q: row["name"]}) + "\">" +
           text +
        "</a>";
    }

    return link("" + services);
  };


});
