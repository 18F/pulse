var Utils = {
  percent: function(num, denom) {
    return Math.round((num / denom) * 100);
  },

  // used to append a cachebusting URL
  cacheBust: function() {
    return "?" + (new Date()).getTime();
  },

  truncate: function (string, length) {
    if (string.length > length)
      return string.substring(0, length) + "...";
    else
      return string;
  },

  // Filter the table on initialization, if the query string says so.
  searchLinks: function(table) {
    var api = table.api();
    var query = QueryString.parse(location.hash).q;

    if (query) {
      $("input[type=search]").val(query);
      api.search(query).draw();
    }
  },

  detailsKeyboardCtrl: function() {
    $('table tbody tr th:first-child').each(function(){
      var content = $(this).parent().find("a").html();
      $(this).attr('tabindex','0')
        .attr('aria-label','Select to show additional details about ' + content)
        .attr('aria-expanded', 'false')
        .on('keydown, click',function(e){
          if (e.keyCode == 13 || e.type == "click") {
            var expanded = $(this).attr('aria-expanded') != "true",
              toggleText = expanded ? "hide" : "show";

            $(this).attr('aria-expanded', expanded);
            $(this).attr('aria-label','Select to ' + toggleText + ' additional details about ' + content);
            var self = this;
            if (!e.originalEvent){
              setTimeout(function(){
                $(self).closest('tr')
                  .next('tr.child')
                  .attr('tabindex', '-1')
                  .focus();
              }, 100)
            }

          }
        })
    });
  },

  updatePagination: function() {
    $('div.dataTables_paginate a:first').attr('aria-label','Previous Page');
    $('div.dataTables_paginate a:last').attr('aria-label','Next Page');
    $('div.dataTables_paginate span a').each(function(){
      var pageNum = $(this).html();
      $(this).attr('aria-label', 'Page ' + pageNum);
    });
  }

};
