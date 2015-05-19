$(document).ready(function () {

  $.get("/assets/data/tables/analytics-domains.json", function(data) {
    var prepared = prepareData(data.data);
    renderTable(prepared);
  });

  /**

    Incoming and outgoing rows are the same:

    {
      "Branch": "executive",
      "Domain": "acus.gov",
      "Live": "True",
      "Participates in Analytics": "False",
      "Redirect": "False"
    }
  */

  // TODO: This data should come from the JSON, not the CSV -> JSON.
  var prepareData = function(domains) {
    var prepared = [];
    for (var i=0; i<domains.length; i++) {
      var domain = domains[i];

      // TODO: Move this to the data preparation stage.
      // Filter step:
      if (domain["Live"] == "False")
        continue;

      if (domain["Redirect"] == "True")
        continue;

      if (domain["Branch"] != "executive")
        continue;

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
