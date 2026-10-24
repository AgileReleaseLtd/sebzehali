// Cookie consent bar. Google Analytics ("istatistik") and Google AdSense ("reklam") are loaded only
// after the visitor accepts them; each choice is kept in localStorage. The ids come from the script
// tag's data-ga and data-ads; a purpose without an id isn't asked about. "Kabul et" and "Reddet" on
// the bar answer for every purpose; the form on the privacy page (#cerez-tercih) sets them one by one.
(function () {
  var tag = document.currentScript;
  var ga = tag.getAttribute('data-ga');
  var ads = tag.getAttribute('data-ads');
  var bar = document.getElementById('cerez');
  var form = document.getElementById('cerez-tercih');
  // 'cerez-izni' predates ads and keeps holding the Google Analytics choice.
  var KEYS = { istatistik: 'cerez-izni', reklam: 'reklam-izni' };
  var asked = [];
  if (ga) asked.push('istatistik');
  if (ads) asked.push('reklam');
  if (!asked.length || !bar) return;

  function saved(p) { try { return localStorage.getItem(KEYS[p]); } catch (e) { return null; } }
  function save(p, v) { try { localStorage.setItem(KEYS[p], v); } catch (e) {} }

  // Remove first-party cookies by name prefix. They may be set on the parent domain, so try each level.
  function forget(prefixes) {
    var host = location.hostname.split('.');
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (!prefixes.some(function (p) { return name.indexOf(p) === 0; })) return;
      document.cookie = name + '=; Max-Age=0; path=/';
      for (var i = 0; i < host.length - 1; i++) {
        document.cookie = name + '=; Max-Age=0; path=/; domain=.' + host.slice(i).join('.');
      }
    });
  }

  function loadAnalytics() {
    window['ga-disable-' + ga] = false;
    if (window.gtag) return;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(ga);
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag('js', new Date());
    gtag('config', ga);
  }

  function stopAnalytics() {
    window['ga-disable-' + ga] = true;
    forget(['_ga']);
  }

  // Only pages with ad slots load AdSense; the slots stay hidden for everyone else.
  var adsLoaded = false;
  function loadAds() {
    var slots = document.querySelectorAll('.reklam');
    if (adsLoaded || !slots.length) return;
    adsLoaded = true;
    var s = document.createElement('script');
    s.async = true;
    s.crossOrigin = 'anonymous';
    s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(ads);
    document.head.appendChild(s);
    slots.forEach(function (slot) {
      slot.hidden = false;
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    });
  }

  // Ads already shown can't be taken back, so reload the page without them.
  function stopAds() {
    forget(['__gads', '__gpi', '__eoi']);
    if (adsLoaded) location.reload();
  }

  var ON = { istatistik: loadAnalytics, reklam: loadAds };
  var OFF = { istatistik: stopAnalytics, reklam: stopAds };

  function choose(p, v) {
    save(p, v);
    (v === 'evet' ? ON : OFF)[p]();
  }

  function tick() {
    if (!form) return;
    asked.forEach(function (p) {
      if (form.elements[p]) form.elements[p].checked = saved(p) === 'evet';
    });
  }

  var unanswered = false;
  asked.forEach(function (p) {
    var v = saved(p);
    if (v === 'evet') ON[p]();
    else if (v !== 'hayir') unanswered = true;
  });
  if (unanswered) bar.hidden = false;
  tick();

  // data-cerez="evet" / "hayir" on the bar's buttons.
  document.addEventListener('click', function (ev) {
    var c = ev.target.getAttribute && ev.target.getAttribute('data-cerez');
    if (c !== 'evet' && c !== 'hayir') return;
    bar.hidden = true;
    asked.forEach(function (p) { choose(p, c); });
    tick();
  });

  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      bar.hidden = true;
      asked.forEach(function (p) {
        if (form.elements[p]) choose(p, form.elements[p].checked ? 'evet' : 'hayir');
      });
      var status = form.querySelector('[role=status]');
      if (status) status.textContent = 'Kaydedildi.';
    });
  }
})();
