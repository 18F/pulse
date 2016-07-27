var Utils = {
  // ignores the 'type' and 'row' args if sent as datatables callback

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

  linkDomain: function(data, type, row) {
    if (type == "sort")
      return data;
    else
      return "" +
        "<a href=\"" + row['canonical'] + "\" target=\"blank\">" +
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

  searchLinks: function() {
    var api = this.api();
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
        errorListOutput += "<li><a href=\"/accessibility/domain/" + row['canonical'].replace(/http:\/\//i, '') + "#" + key.replace(/\s/g, '').replace(/\//i, '') + "\" target=\"_blank\">" + key + ": " + value + "</a></li>";
      }
    });

    if (!errorListOutput) {
      return "</hr><span class=\"noErrors\">No errors found.</span>";
    } else {
      return "</hr><ul class=\"errorList\">" + errorListOutput + "</ul></hr>";
    }
  }

};
