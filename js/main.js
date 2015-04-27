$(document).ready(function () {
  
  // Initialize the json call 
  url = "data/data.json"
  sites = []

  // Get the JSON
  $.getJSON(url, function (data) {
    
    // Parse the JSON into individual sites
    $.each(data, function(idx, el) {

      // More code will go here
      // Each site is manipulable here
      sites.push(el["canonical"])
    })

    // This happens when everything is done
    console.log(sites)
  })
})