// $(document).ready(function () {

//   $.get("/assets/data/tables/https-agency.json", function(data) {
//     renderTable(data.data);
//   });

//   var renderTable = function(data) {
//     $("table").DataTable({

//       data: data,

//       columns: [
//         {"data":"Agency name" },
//         {"data":"# of Domains"},
//         {"data":"% Using HTTPS"},
//         {"data":"% Strictly Enforcing HTTPS"},
//         {"data":"% Using HSTS"},
//       ],

//       "oLanguage": {
//         "oPaginate": {
//           "sPrevious": "<<",
//           "sNext": ">>"
//         }
//       },

//     });
//   };

// })

$(document).ready(function() {
    $('table').dataTable( {
        "oLanguage": {
        "oPaginate": {
          "sPrevious": "<<",
          "sNext": ">>"
        }
      },
    } );
});