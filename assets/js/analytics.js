$(document).ready(function () {

  $.get("/assets/data/tables/analytics-domains.json", function(data) {
    var prepared = prepareData(data.data);
    renderTable(prepared);
  });

  /**

    Incoming and outgoing rows are the same:

    {
      "Domain": "abandonedmines.gov",
      "Participates in Analytics": "False"
    }
  */

  // TODO: This data should come from the JSON, not the CSV -> JSON.
  var prepareData = function(domains) {
    var prepared = [];
    for (var i=0; i<domains.length; i++) {
      var domain = domains[i];

      // TODO: Filter out non-exec domains.
      // TODO: Filter out non-live domains.
      // TODO: Filter out redirect domains.

      prepared.push(domain);
    }

    return prepared;
  }


  var renderTable = function(data) {
    $("table").DataTable({
      data: data,

      columns: [
        {"data":"Domain"},
        {"data":"Participates in Analytics"}
      ],

      dom: "lrtip"
    });
  };

});
