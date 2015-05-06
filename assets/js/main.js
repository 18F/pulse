$(document).ready(function () {


  $('#mainTableId').DataTable({
    "ajax": "/assets/data/domainData.json",
    "columns": [
      {"data":"Domain"},
      {"data":"Canonical"},
      {"data":"Live"},
      {"data":"Redirect"},
      {"data":"Redirect To"},
      {"data":"Valid HTTPS"},
      {"data":"Defaults to HTTPS"},
      {"data":"Downgrades HTTPS"},
      {"data":"Strictly Forces HTTPS"},
      {"data":"HTTPS Bad Chain"},
      {"data":"HTTPS Bad Hostname"},
      {"data":"HSTS"},
      {"data":"HSTS Header"},
      {"data":"HSTS All Subdomains"},
      {"data":"HSTS Preload Ready"},
      {"data":"Broken Root"},
      {"data":"Broken WWW"}
    ]
  });

})