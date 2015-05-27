$(function(){
  $('#menu-btn,.overlay,.sliding-panel-close').on('click touchstart',function (e) {
    $('#menu-content,.overlay').toggleClass('is-visible');
    e.preventDefault();
  });
});
