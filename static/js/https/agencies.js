$(document).ready(function () {

  $.get("/data/agencies/https.json", function(data) {
    renderTable(data.data);
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

    return "<b>" + services + "</b> services" + "<br/>in " + link("" + domains + " domains");
  };

  // report: e.g. 'https', or 'crypto'
  // field: e.g. 'uses' or 'rc4'
  var percentBar = function(report, field) {
    return function(data, type, row) {
      var percent = Utils.percent(
        row[report][field], row[report].eligible
      );

      if (type == "sort") return percent;
      else return Utils.progressBar(percent);
    };
  };

  var renderTable = function(data) {
    var table = $("table").DataTable({
      initComplete: Utils.searchLinks,

      responsive: {
          details: {
              type: "",
              display: $.fn.dataTable.Responsive.display.childRowImmediate
          }
      },

      data: data,

      // order by number of domains
      order: [[1, "desc"]],

      columnDefs: [
        {
          cellType: "th",
          createdCell: function (td) {
            td.scope = "row";
          },
          data: "name",
          targets: 0
        },
        {
          data: "https.eligible", // sort on this, but
          render: eligibleHttps,
          targets: 1,
        },
        {
          data: "https.enforces",
          render: percentBar("https", "enforces"),
          targets: 2,
        },
        {
          data: "https.hsts",
          render: percentBar("https", "hsts"),
          targets: 3,
        },
        {
          data: "crypto.bod_crypto",
          render: percentBar("crypto", "bod_crypto"),
          targets: 4,
        },
        {
          data: "preloading.preloaded",
          render: percentBar("preloading", "preloaded"),
          targets: 5,
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
