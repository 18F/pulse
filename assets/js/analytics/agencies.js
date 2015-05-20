// $(document).ready(function () {

//   $.get("/assets/data/tables/analytics/agencies.json", function(data) {
//     renderTable(data.data);
//   });

//   var renderTable = function(data) {
//     $("table").DataTable({
//       data: data,

//       columns: [
//         {"data":"Domain"},
//         {"data":"Participates in DAP?"}
//       ],

//       "oLanguage": {
//         "oPaginate": {
//           "sPrevious": "<<",
//           "sNext": ">>"
//         }
//       },

//     });
//   };

// });

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
