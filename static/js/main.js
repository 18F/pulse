$(function(){

  $('#menu-btn, .overlay, .sliding-panel-close').on('click touchstart',function (e) {
    $('#menu-content, .overlay').toggleClass('is-visible');
    e.preventDefault();
  });

  // if a datatable is searched, sync it to the URL hash
  $('table').on('search.dt', function(e, settings) {
    var query = $("input[type=search]").val();
    if (query)
      location.hash = QueryString.stringify({q: query});
    // TODO: Disabled because this callback runs on table init,
    // and zeroes out the location hash. Should be addressed.
    // else
    //   location.hash = '';
  });

});
