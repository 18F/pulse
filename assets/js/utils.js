
var Utils = {
  // ignores the 'type' and 'row' args if sent as datatables callback


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
        "<a href=\"" + row['Canonical'] + "\" target=\"blank\">" +
          data +
        "</a>";
  },

  // used to make "71" say "71 domains" and link to filtered domains
  linkAgency: function(page) {
    return function(data, type, row) {
      if (type == "sort")
        return data;
      else
        return "" +
          "<a href=\"/" + page + "/domains/#" +
            QueryString.stringify({q: row["Agency"]}) + "\">" +
            data +
          "</a>";
    }
  },

  searchLinks: function() {
    var api = this.api();
    var query = QueryString.parse(location.hash).q;

    if (query) {
      $("input[type=search]").val(query);
      api.search(query).draw();
    }
  }
};
