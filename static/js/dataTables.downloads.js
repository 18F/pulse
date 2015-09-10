/**
 * Downloadable CSV links.
 *
 * @example
 *   $('#myTable').DataTable( {
 *     dom: 'Cfrtip',
 *     csv: '/path/to/data.csv'
 *   } );
 */

(function(window, document, $, undefined) {


$.fn.dataTable.Download = function ( inst ) {
  var api = new $.fn.dataTable.Api( inst );
  var settings = api.settings()[0];

  var csv = settings.oInit.csv;

  var container = $('<div></div>').addClass( 'dataTables_csv' );
  var drawnOnce = false;

  // API so the feature wrapper can return the node to insert
  this.container = function () {
    return container[0];
  };

  api.on('draw', function () {
    if (drawnOnce) return;

    var elem = "" +
      "<a href=\"" + csv + "\" download>" +
        "Download CSV" +
      "</a>";

    container.html(elem);
    drawnOnce = true;
  });
};

// Subscribe the feature plug-in to DataTables, ready for use
$.fn.dataTable.ext.feature.push( {
  "fnInit": function( settings ) {
    var l = new $.fn.dataTable.Download(settings);
    return l.container();
  },
  "cFeature": "C",
  "sFeature": "Downloads"
} );


})(window, document, jQuery);
