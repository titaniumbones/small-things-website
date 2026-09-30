// Calendar series filter. Without JavaScript the full list is shown and the buttons are hidden.
(function () {
  var bar = document.querySelector('[data-filters]');
  if (!bar) return;
  var buttons = Array.prototype.slice.call(bar.querySelectorAll('[data-filter]'));
  var groups = Array.prototype.slice.call(document.querySelectorAll('[data-event-groups]'));
  var empty = document.querySelector('[data-empty]');

  function apply(series) {
    buttons.forEach(function (b) {
      var on = b.getAttribute('data-filter') === series;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    var shownAnywhere = false;
    groups.forEach(function (g) {
      Array.prototype.forEach.call(g.querySelectorAll('[data-month]'), function (month) {
        var visible = 0;
        Array.prototype.forEach.call(month.querySelectorAll('.event-row'), function (row) {
          var show = series === 'all' || row.getAttribute('data-series') === series;
          row.hidden = !show;
          if (show) visible++;
        });
        month.hidden = visible === 0;
        if (visible) shownAnywhere = true;
      });
    });
    if (empty) empty.hidden = shownAnywhere;
    try { history.replaceState(null, '', series === 'all' ? location.pathname : '#' + series); } catch (e) {}
  }

  buttons.forEach(function (b) {
    b.addEventListener('click', function () { apply(b.getAttribute('data-filter')); });
  });

  var initial = location.hash.replace('#', '');
  if (initial && buttons.some(function (b) { return b.getAttribute('data-filter') === initial; })) apply(initial);
})();
