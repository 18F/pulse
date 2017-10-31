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

    return link("" + services);
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

      initComplete: function() {
        Utils.searchLinks(this);
      },

      responsive: {
          details: {
              type: "",
              display: $.fn.dataTable.Responsive.display.childRowImmediate
          }
      },

      data: data,

      lengthChange: false,
      pageLength: 150,

      // order by number of domains
      order: [[1, "desc"]],

      columns: [
        {
          cellType: "th",
          createdCell: function (td) {
            td.scope = "row";
          },
          data: "name"
        },
        {
          data: "https.eligible", // sort on this, but
          render: eligibleHttps,
          type: "num"
        },
        {
          data: "https.compliant",
          render: percentBar("https", "enforces"),
          className: "compliant",
          width: "100px"
        },
        {
          data: "https.enforces",
          render: percentBar("https", "enforces")
        },
        {
          data: "https.hsts",
          render: percentBar("https", "hsts")
        },
        {
          data: "crypto.bod_crypto",
          render: percentBar("crypto", "bod_crypto")
        },
        {
          data: "preloading.preloaded",
          render: percentBar("preloading", "preloaded")
        }
      ],

      "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      },

      csv: "/data/hosts/https.csv",
      dom: 'Cftri'

    });

    Utils.updatePagination();
    table.on("draw.dt",function(){
      Utils.updatePagination();
    });
  };

});
