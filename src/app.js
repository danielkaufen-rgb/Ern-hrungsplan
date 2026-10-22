(function(){
  'use strict';
  var $ = function(s, r){ return (r || document).querySelector(s); };
  var $$ = function(s, r){ return Array.prototype.slice.call((r || document).querySelectorAll(s)); };
  var store = {
    get: function(k){ try{ return JSON.parse(localStorage.getItem(k)); }catch(e){ return null; } },
    set: function(k, v){ try{ localStorage.setItem(k, JSON.stringify(v)); }catch(e){} }
  };
  var reduceMotion = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function norm(s){ return String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ß/g, 'ss'); }

  // ---------- Hinweis ----------
  var toastEl = $('#toast'), toastT = null;
  function toast(msg){
    toastEl.textContent = msg;
    toastEl.classList.add('on');
    clearTimeout(toastT);
    toastT = setTimeout(function(){ toastEl.classList.remove('on'); }, 2200);
  }

  // ---------- Hell / Dunkel ----------
  function setTheme(t){
    document.documentElement.setAttribute('data-theme', t);
    try{ localStorage.setItem('ep-theme', t); }catch(e){}
    var m = $('meta[name="theme-color"]');
    if(m) m.content = t === 'dark' ? '#000000' : '#f2f2f7';
  }
  document.addEventListener('click', function(e){
    if(!e.target.closest('[data-theme-toggle]')) return;
    setTheme(document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
  });

  // ---------- Seiten und Navigation ----------
  var pages = {};
  $$('.page').forEach(function(p){ pages[p.getAttribute('data-route')] = p; });
  var TABS = ['heute', 'rezepte', 'woche', 'einkauf', 'wissen'];
  var TABNAME = {heute:'Heute', rezepte:'Rezepte', woche:'Woche', einkauf:'Einkauf', wissen:'Wissen'};
  var segBtns = $$('#seg [data-cat]');
  var CATS = segBtns.map(function(b){ return b.getAttribute('data-cat'); });
  var cat = (function(){
    var h = new Date().getHours() + new Date().getMinutes() / 60;
    return h < 10.5 ? 'fruehstueck' : h < 15 ? 'mittagessen' : h < 17.5 ? 'snacks' : 'abendessen';
  })();
  var curRoute = null, curTab = 'heute', stack = [], scrolls = {}, ownerOf = {};
  var tabLast = {}; TABS.forEach(function(t){ tabLast[t] = t; });

  function isRoot(r){ return TABS.indexOf(r) >= 0; }
  function rootHash(tab){ return tab === 'rezepte' ? 'rezepte/' + cat : tab; }
  function parse(h){
    h = (h || '').replace(/^#\/?/, '');
    try{ h = decodeURIComponent(h); }catch(e){}
    if(!h) return {route:'heute'};
    var m = h.match(/^rezepte(?:\/(.+))?$/);
    if(m) return {route:'rezepte', cat: CATS.indexOf(m[1]) >= 0 ? m[1] : null};
    if(pages[h]) return {route:h};
    if(pages['r/' + h]) return {route:'r/' + h};
    if(CATS.indexOf(h) >= 0) return {route:'rezepte', cat:h};
    if(pages['w/' + h]) return {route:'w/' + h};
    return {route:'heute'};
  }
  function ownerFor(route){
    var from = curRoute === null ? null : curTab;
    if(isRoot(route)) return route;
    if(route.indexOf('w/') === 0) return from === 'heute' ? 'heute' : 'wissen';
    if(route.indexOf('r/') === 0) return (from === 'heute' || from === 'woche') ? from : 'rezepte';
    return 'heute';
  }
  function show(route, dir){
    var page = pages[route];
    if(!page) return;
    if(curRoute) scrolls[curRoute] = window.scrollY;
    var tab = isRoot(route) ? route : (dir === 'pop' && ownerOf[route]) ? ownerOf[route] : ownerFor(route);
    ownerOf[route] = tab;
    tabLast[tab] = route;
    curTab = tab;
    Object.keys(pages).forEach(function(k){
      if(k === route || pages[k].hidden) return;
      pages[k].hidden = true;
      pages[k].classList.remove('scrolled', 'titled');
    });
    page.hidden = false;
    var back = $('.back', page);
    if(back){
      $('.back-t', back).textContent = TABNAME[tab];
      back.setAttribute('href', '#' + rootHash(tab));
      back.setAttribute('aria-label', 'Zurück zu ' + TABNAME[tab]);
    }
    $$('[data-tab]').forEach(function(a){
      if(a.getAttribute('data-tab') === tab) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    });
    var prevRoute = curRoute;
    curRoute = route;
    document.title = (page.getAttribute('data-title') || 'Ernährungsplan') + ' · Ernährungsplan';
    if(prevRoute !== null && prevRoute !== route && !reduceMotion){
      var cls = dir === 'pop' ? 'anim-pop' : dir === 'push' && !isRoot(route) ? 'anim-push' : 'anim-fade';
      page.classList.remove('anim-push', 'anim-pop', 'anim-fade');
      void page.offsetWidth;
      page.classList.add(cls);
    }
    var y = (dir === 'pop' || isRoot(route)) ? (scrolls[route] || 0) : 0;
    window.scrollTo(0, y);
    onScroll();
    if(route.indexOf('r/') !== 0 && wakeWanted) wakeOff(true);
    paintWake();
  }
  function onHash(){
    var p = parse(location.hash), r = p.route, dir = 'push';
    if(p.cat) setCat(p.cat, true);
    if(stack.length > 1 && stack[stack.length - 2] === r){ stack.pop(); dir = 'pop'; }
    else if(stack[stack.length - 1] !== r){ stack.push(r); }
    if(isRoot(r) && (curRoute === null || isRoot(curRoute))) dir = 'tab';
    show(r, dir);
  }
  function go(h){
    if(location.hash === '#' + h) onHash(); else location.hash = h;
  }
  window.addEventListener('hashchange', onHash);
  document.addEventListener('click', function(e){
    var t = e.target.closest('[data-tab]');
    if(t){
      e.preventDefault();
      var tab = t.getAttribute('data-tab');
      if(tab === curTab){
        if(curRoute !== tab){
          if(stack.length > 1 && stack[stack.length - 2] === tab) history.back(); else go(rootHash(tab));
        } else {
          window.scrollTo({top:0, behavior: reduceMotion ? 'auto' : 'smooth'});
        }
      } else {
        go(tabLast[tab] === 'rezepte' ? rootHash('rezepte') : tabLast[tab]);
      }
      return;
    }
    var b = e.target.closest('[data-back]');
    if(b){
      e.preventDefault();
      goBack();
    }
  });
  function goBack(){
    if(isRoot(curRoute)) return;
    if(stack.length > 1) history.back();
    else { stack = []; location.replace('#' + rootHash(curTab)); }
  }
  document.addEventListener('keydown', function(e){
    if(e.key === 'Escape' && curRoute && !isRoot(curRoute) && !e.target.closest('input')) goBack();
  });

  // Große Titel: kleiner Titel in der Leiste, sobald der große weggescrollt ist
  var ticking = false;
  function onScroll(){
    var page = pages[curRoute];
    if(!page) return;
    var nav = $('.nav', page), lt = $('.lt', page);
    var navB = nav ? nav.getBoundingClientRect().bottom : 56;
    page.classList.toggle('scrolled', window.scrollY > 4);
    var ttl = lt ? $('.ltitle', lt) : null;
    page.classList.toggle('titled', !!ttl && ttl.getBoundingClientRect().bottom < navB - 4);
  }
  window.addEventListener('scroll', function(){
    if(ticking) return;
    ticking = true;
    requestAnimationFrame(function(){ ticking = false; onScroll(); });
  }, {passive:true});

  // ---------- Rezepte: Kategorien, Filter, Suche ----------
  var seg = $('#seg'), recipePage = pages['rezepte'];
  function setCat(c, fromHash){
    if(CATS.indexOf(c) < 0) return;
    var changed = c !== cat;
    cat = c;
    var i = CATS.indexOf(c);
    seg.style.setProperty('--i', i);
    segBtns.forEach(function(b){ b.setAttribute('aria-selected', b.getAttribute('data-cat') === c ? 'true' : 'false'); });
    if(!recipePage.classList.contains('searching')){
      $$('.cat', recipePage).forEach(function(el){ el.hidden = el.getAttribute('data-cat') !== c; });
    }
    if(!fromHash && curRoute === 'rezepte' && history.replaceState) history.replaceState(null, '', '#rezepte/' + c);
    if(changed && !fromHash && curRoute === 'rezepte'){
      var top = seg.getBoundingClientRect().top + window.scrollY - 70;
      if(window.scrollY > top) window.scrollTo(0, top);
    }
  }
  seg.addEventListener('click', function(e){
    var b = e.target.closest('[data-cat]');
    if(b) setCat(b.getAttribute('data-cat'));
  });
  seg.addEventListener('keydown', function(e){
    if(e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    var i = CATS.indexOf(cat) + (e.key === 'ArrowRight' ? 1 : -1);
    i = (i + CATS.length) % CATS.length;
    setCat(CATS[i]);
    segBtns[i].focus();
  });
  setCat(cat, true);

  $$('.chips').forEach(function(f){
    var list = f.parentElement.querySelector('.rlist');
    f.addEventListener('click', function(e){
      var b = e.target.closest('.chip');
      if(!b) return;
      $$('.chip', f).forEach(function(x){ x.classList.toggle('on', x === b); });
      var k = b.getAttribute('data-f');
      $$('.rrow', list).forEach(function(r){ r.classList.toggle('hide', k !== 'all' && r.getAttribute('data-kind') !== k); });
    });
  });

  var q = $('#q'), qx = $('#qx'), noRes = $('#noRes');
  $$('.rrow').forEach(function(r){ r._q = norm(r.getAttribute('data-q') || ''); });
  function applySearch(){
    var term = norm(q.value.trim());
    qx.hidden = !q.value;
    recipePage.classList.toggle('searching', !!term);
    if(!term){
      $$('.rrow', recipePage).forEach(function(r){ r.classList.remove('nomatch'); });
      $$('.cat', recipePage).forEach(function(el){ el.hidden = el.getAttribute('data-cat') !== cat; });
      noRes.hidden = true;
      return;
    }
    var words = term.split(/\s+/), any = false;
    $$('.cat', recipePage).forEach(function(el){
      var n = 0;
      $$('.rrow', el).forEach(function(r){
        var ok = words.every(function(w){ return r._q.indexOf(w) >= 0; });
        r.classList.toggle('nomatch', !ok);
        if(ok) n++;
      });
      el.hidden = n === 0;
      if(n) any = true;
    });
    noRes.hidden = any;
  }
  q.addEventListener('input', applySearch);
  q.addEventListener('keydown', function(e){ if(e.key === 'Escape'){ q.value = ''; applySearch(); } });
  qx.addEventListener('click', function(){ q.value = ''; applySearch(); q.focus(); });

  // ---------- Heute und Woche ----------
  var SLOTS = [['Frühstück', 'orange'], ['Mittag', 'green'], ['Snack', 'teal'], ['Abend', 'indigo']];
  var dow = (new Date().getDay() + 6) % 7;
  function kNum(s){ return parseFloat(String(s).replace(/\./g, '').replace(',', '.')) || 0; }
  function sumCard(w, label, isToday){
    var bar = w.meals.map(function(m, i){ return '<i class="b-' + SLOTS[i][1] + '" style="flex:' + kNum(m[3]) + '"></i>'; }).join('');
    var aria = w.meals.map(function(m, i){ return SLOTS[i][0] + ' ' + m[3] + ' kcal'; }).join(', ');
    var legend = w.meals.map(function(m, i){
      return '<span><i class="dot b-' + SLOTS[i][1] + '"></i>' + SLOTS[i][0] + ' <b class="num">' + m[3] + '</b></span>';
    }).join('');
    return '<div class="sum-top"><div><div class="sum-l">' + esc(label) + (isToday ? ' <span class="badge">Heute</span>' : '') + '</div>' +
      '<div class="sum-k num">' + w.k + '<small> kcal</small></div></div>' +
      '<div class="sum-side"><div><b class="num">' + w.p.replace(' g', '') + '<span class="u"> g</span></b><small>Protein</small></div></div></div>' +
      '<div class="bar" role="img" aria-label="' + esc('Kalorien: ' + aria) + '">' + bar + '</div>' +
      '<div class="legend">' + legend + '</div>';
  }
  function mealRows(w){
    return w.meals.map(function(m, i){
      return '<a class="row" href="#r/' + m[1] + '"><span class="tile t-' + SLOTS[i][1] + '" aria-hidden="true">' + m[2] + '</span>' +
        '<span class="rtx"><span class="rcap c-' + SLOTS[i][1] + '">' + SLOTS[i][0] + '</span><span class="rtt">' + esc(m[0]) + '</span>' +
        '<span class="rmeta">' + esc(m[5]) + ' · <span class="num">' + m[3] + ' kcal</span> · <span class="num">' + m[4] + '</span> Protein</span></span>' +
        '<svg class="chev" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.6 1.6 6.4 7l-4.8 5.4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></a>';
    }).join('');
  }
  var today = WEEK[dow];
  try{
    $('#todayDate').textContent = new Date().toLocaleDateString('de-DE', {weekday:'long', day:'numeric', month:'long'});
  }catch(e){ $('#todayDate').textContent = today.n; }
  $('#todaySum').innerHTML = sumCard(today, 'Tagesplan', false);
  $('#todayList').innerHTML = mealRows(today);

  var dayBtns = $$('#days .day'), weekRows = $$('#weekList .wrow');
  dayBtns[dow].classList.add('today');
  weekRows[dow].classList.add('today');
  function selectDay(i){
    dayBtns.forEach(function(b, j){ b.setAttribute('aria-selected', i === j ? 'true' : 'false'); });
    weekRows.forEach(function(r, j){ r.classList.toggle('sel', i === j); });
    $('#daySum').innerHTML = sumCard(WEEK[i], WEEK[i].n, i === dow);
    $('#dayList').innerHTML = mealRows(WEEK[i]);
  }
  $('#days').addEventListener('click', function(e){
    var b = e.target.closest('.day');
    if(b) selectDay(+b.getAttribute('data-day'));
  });
  $('#weekList').addEventListener('click', function(e){
    var r = e.target.closest('.wrow');
    if(!r) return;
    selectDay(+r.getAttribute('data-day'));
    var top = $('#days').getBoundingClientRect().top + window.scrollY - 72;
    window.scrollTo({top: top, behavior: reduceMotion ? 'auto' : 'smooth'});
  });
  selectDay(dow);

  // ---------- Einkaufsliste (bleibt im Browser gespeichert) ----------
  (function(){
    var boxes = $$('input[data-key="shop"]');
    if(!boxes.length) return;
    var saved = store.get('ep3-shop') || {};
    // Häkchen hängen am Namen des Eintrags: Was nicht mehr auf der Liste steht, fliegt raus
    var keys = boxes.map(function(b){ return b.getAttribute('data-i'); });
    Object.keys(saved).forEach(function(k){ if(keys.indexOf(k) < 0) delete saved[k]; });
    store.set('ep3-shop', saved);
    var ring = $('#shopRing'), C = parseFloat(ring.getAttribute('stroke-dasharray'));
    var lists = $('#shopLists'), hideBtn = $('#hideDone');
    function upd(){
      boxes.forEach(function(b){ var l = b.closest('.ck'); if(l) l.classList.toggle('done', b.checked); });
      var n = boxes.filter(function(b){ return b.checked; }).length;
      $('#shopCount').textContent = n === boxes.length ? 'Alles erledigt' : n + ' von ' + boxes.length;
      $('#shopSub').textContent = n === boxes.length ? boxes.length + ' Einträge abgehakt' : 'erledigt';
      ring.style.strokeDashoffset = C * (1 - n / boxes.length);
    }
    boxes.forEach(function(b){
      b.checked = !!saved[b.getAttribute('data-i')];
      b.addEventListener('change', function(){
        saved[b.getAttribute('data-i')] = b.checked;
        store.set('ep3-shop', saved);
        upd();
      });
    });
    $('[data-reset="shop"]').addEventListener('click', function(){
      if(!boxes.some(function(b){ return b.checked; })) return;
      saved = {}; store.set('ep3-shop', saved);
      boxes.forEach(function(b){ b.checked = false; });
      upd();
      toast('Alle Häkchen entfernt');
    });
    function paintHide(on){
      lists.classList.toggle('hide-done', on);
      hideBtn.setAttribute('aria-pressed', on ? 'true' : 'false');
      hideBtn.textContent = on ? 'Erledigte zeigen' : 'Erledigte ausblenden';
    }
    hideBtn.addEventListener('click', function(){
      var on = hideBtn.getAttribute('aria-pressed') !== 'true';
      store.set('ep-shop-hide', on);
      paintHide(on);
    });
    paintHide(!!store.get('ep-shop-hide'));
    upd();
  })();

  // ---------- Schritte abhaken (laufen nach 2 Stunden ab) ----------
  var STEP_TTL = 2 * 60 * 60 * 1000;
  var steps = store.get('ep-steps') || {};
  function pruneSteps(){
    var now = Date.now(), changed = false;
    Object.keys(steps).forEach(function(k){ if(now - steps[k] >= STEP_TTL){ delete steps[k]; changed = true; } });
    if(changed) store.set('ep-steps', steps);
    return changed;
  }
  var stepLists = $$('ol.steps').map(function(ol){
    var items = $$(':scope > li', ol);
    var bar = ol.previousElementSibling && ol.previousElementSibling.classList.contains('stepbar') ? ol.previousElementSibling : null;
    items.forEach(function(li){
      var key = li.getAttribute('data-step');
      $('.stepck', li).addEventListener('click', function(){
        if(steps[key]) delete steps[key]; else steps[key] = Date.now();
        store.set('ep-steps', steps);
        paintSteps();
      });
    });
    if(bar) $('.sreset', bar).addEventListener('click', function(){
      items.forEach(function(li){ delete steps[li.getAttribute('data-step')]; });
      store.set('ep-steps', steps);
      paintSteps();
    });
    return {items:items, bar:bar};
  });
  function paintSteps(){
    stepLists.forEach(function(l){
      var n = 0;
      l.items.forEach(function(li){
        var on = !!steps[li.getAttribute('data-step')];
        li.classList.toggle('done', on);
        $('.stepck', li).setAttribute('aria-pressed', on ? 'true' : 'false');
        if(on) n++;
      });
      if(l.bar){
        $('.sc', l.bar).textContent = n + ' von ' + l.items.length;
        $('.sp i', l.bar).style.width = (100 * n / l.items.length) + '%';
      }
    });
  }
  pruneSteps(); paintSteps();
  setInterval(function(){ if(pruneSteps()) paintSteps(); }, 30000);

  // ---------- Kochmodus: Bildschirm bleibt an ----------
  var canWake = 'wakeLock' in navigator, wakeLock = null, wakeWanted = false;
  if(canWake) $$('.wake').forEach(function(b){ b.hidden = false; });
  function paintWake(){
    $$('.wake').forEach(function(b){ b.setAttribute('aria-pressed', wakeWanted ? 'true' : 'false'); });
  }
  function wakeOn(){
    if(!canWake) return;
    navigator.wakeLock.request('screen').then(function(s){
      wakeLock = s;
      s.addEventListener('release', function(){ wakeLock = null; });
    }).catch(function(){
      wakeWanted = false; paintWake();
      toast('Kochmodus geht hier leider nicht');
    });
  }
  function wakeOff(silent){
    wakeWanted = false;
    if(wakeLock){ wakeLock.release(); wakeLock = null; }
    paintWake();
    if(!silent) toast('Kochmodus aus');
  }
  document.addEventListener('click', function(e){
    if(!e.target.closest('.wake')) return;
    if(wakeWanted){ wakeOff(); return; }
    wakeWanted = true; paintWake(); wakeOn();
    toast('Kochmodus an: Der Bildschirm bleibt an');
  });
  document.addEventListener('visibilitychange', function(){
    if(document.hidden) return;
    if(pruneSteps()) paintSteps();
    if(wakeWanted && !wakeLock && curRoute && curRoute.indexOf('r/') === 0) wakeOn();
  });

  // ---------- Start ----------
  onHash();
})();
