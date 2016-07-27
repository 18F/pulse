$(document).ready(function () {

  var domain = $('#main-content').data('domain'),
      $element = $('.a11y');

  $.get("/static/data/tables/accessibility/a11y.json", function(data) {

    for (var key in data.data) {

      if (key === domain) {

        var categories = data.data[key];
        for (var category in categories) {

          if (categories[category].length) {

            $element.append(
              '<div id="' + category.replace(/\s/g, '').replace(/\//i, '') + '" class="category">' +
              '<h2>' + category + ' (' + categories[category].length + ')</h2>' +
              '<ul></ul>' +
              '</div>'
            );

          }

          $(categories[category]).each(function(key, error)  {
            $list = $('ul').last();

            $list.append(
              '<li>' +
              '<div class="code">' + error['code'] + '</div>' +
              '<div class="selector"><span>Selector:</span> ' + error['selector'] + '</div>' +
              '<div class="context"><span>Context:</span> <code>' + error['context'].replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;') +
              '</code></div>' +
              '<div class="description"><span>Description:</span> ' + error['description'] +
              '</div></li>'
            );
          });

        }
      }
    }

    if(!$element.html()) {
      $element.html('No results found for ' + domain);
    }

  }).done(function () {

    // if url hash present, scroll to div
    if (window.location.hash) {
      $('html, body').scrollTop(parseInt($(location.hash).offset().top));
    }

  });

});
