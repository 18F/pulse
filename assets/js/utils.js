
var Utils = {
  // ignores the 'type' and 'row' args if sent as datatables callback
  progressBar: function(data) {
    return '' +
      '<div class="progress-bar-indication">' +
        '<span class="meter" style="width: ' + data + '%">' +
          '<p>' + data + '%</p>' +
        '</span>' +
      '</div>';
  }
};
