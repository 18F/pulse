var Utils = {
  percent: function(num, denom) {
    return Math.round((num / denom) * 100);
  },

  progressBar: function(data) {
    return '' +
      '<div class="progress-bar-indication">' +
        '<span class="meter width' + data + '" style="width: ' + data + '%">' +
          '<p>' + data + '%</p>' +
        '</span>' +
      '</div>';
  },

  truncate: function (string, length) {
    if (string.length > length)
      return string.substring(0, length) + "...";
    else
      return string;
  },

  linkDomain: function(data, type, row) {
    if (type == "sort")
      return data;
    else
      return "" +
        "<a href=\"" + row.canonical + "\" target=\"blank\">" +
          data +
        "</a>";
  },

  // used to make "71" say "71 domains" and link to filtered domains
  filterAgency: function(page) {
    return function(data, type, row) {
      if (type == "sort")
        return data;
      else
        return "" +
          "<a href=\"/" + page + "/domains/#" +
            QueryString.stringify({q: row["name"]}) + "\">" +
            data +
          "</a>";
    };
  },

  searchLinks: function(table) {
    var api = table.api();
    var query = QueryString.parse(location.hash).q;

    if (query) {
      $("input[type=search]").val(query);
      api.search(query).draw();
    }
  },

  a11yErrorList: function(data, type, row) {
    var errorListOutput = "";

    $.each(data, function(key, value) {
      if (value) {
        errorListOutput += "<li><a href=\"/a11y/domain/" + row['domain'].replace(/http:\/\//i, '') + "#" + key.replace(/\s/g, '').replace(/\//i, '') + "\" target=\"_blank\">" + key + ": " + value + "</a></li>";
      }
    });

    if (!errorListOutput) {
      return "</hr><span class=\"noErrors\">No errors found.</span>";
    } else {
      return "</hr><ul class=\"errorList\">" + errorListOutput + "</ul></hr>";
    }
  },

  custSatList: function(data, type, row) {
    var custSatListOutput = "";

    $.each(data, function(key, value) {
      if (value) {
        custSatListOutput += "<li><a href=\"" + value + "\">" + key + "</a></li>";
      }
    });

    if (!custSatListOutput) {
      return "</hr><span class=\"noErrors\">No customer satisfaction tools used.</span>";
    } else {
      return "</hr><ul class=\"errorList\">" + custSatListOutput + "</ul></hr>";
    }
  },

  detailsKeyboardCtrl: function(){
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

  updatePagination: function(){
    $('div.dataTables_paginate a:first').attr('aria-label','Previous Page');
    $('div.dataTables_paginate a:last').attr('aria-label','Next Page');
    $('div.dataTables_paginate span a').each(function(){
      var pageNum = $(this).html();
      $(this).attr('aria-label', 'Page ' + pageNum);
    });
  }

};
