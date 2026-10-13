// Cookie consent bar. Google Analytics is loaded only after the visitor picks "Kabul et";
// the choice is kept in localStorage. The measurement id comes from the script tag's data-ga.
(function () {
  var id = document.currentScript.getAttribute('data-ga');
  var bar = document.getElementById('cerez');
  var KEY = 'cerez-izni';
  if (!id || !bar) return;

  function saved() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(v) { try { v ? localStorage.setItem(KEY, v) : localStorage.removeItem(KEY); } catch (e) {} }

  function load() {
    window['ga-disable-' + id] = false;
    if (window.gtag) return;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(id);
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag('js', new Date());
    gtag('config', id);
  }

  // Stop sending and remove the _ga cookies (set on the parent domain, so try each level).
  function stop() {
    window['ga-disable-' + id] = true;
    var host = location.hostname.split('.');
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (name.indexOf('_ga') !== 0) return;
      document.cookie = name + '=; Max-Age=0; path=/';
      for (var i = 0; i < host.length - 1; i++) {
        document.cookie = name + '=; Max-Age=0; path=/; domain=.' + host.slice(i).join('.');
      }
    });
  }

  var choice = saved();
  if (choice === 'evet') load();
  else if (choice !== 'hayir') bar.hidden = false;

  // data-cerez="evet" / "hayir" on the bar's buttons; "sor" on the privacy page asks again.
  document.addEventListener('click', function (ev) {
    var c = ev.target.getAttribute && ev.target.getAttribute('data-cerez');
    if (!c) return;
    if (c === 'sor') { stop(); save(null); bar.hidden = false; return; }
    save(c);
    bar.hidden = true;
    if (c === 'evet') load(); else stop();
  });
})();
