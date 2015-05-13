$(document).ready(function () {

  $("table").DataTable({
    ajax: "/assets/data/tables/analytics-domains.json",
    columns: [
      {"data":"Domain"},
      {"data":"Participating"}
    ],
    dom: "lrtip"
  });

});
