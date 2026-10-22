const { chromium } = require('playwright');
const path = require('path');
const FILE = 'file://' + path.resolve(process.argv[2] || path.join(__dirname, '..', 'index.html'));
const fails = [];
function ok(cond, msg){ if(!cond) fails.push(msg); else console.log('  ✓ ' + msg); }
(async () => {
  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', e => errs.push(e.message));
  await page.addInitScript(() => { if (!sessionStorage.getItem('seeded')) { localStorage.setItem('ep3-shop', JSON.stringify({'0': true, '5': true, '12': true})); sessionStorage.setItem('seeded', '1'); } });
  await page.goto(FILE);
  ok((await page.textContent('#shopCount')) === '0 von 63', 'Alte Index-Häkchen werden ignoriert');
  ok(await page.evaluate(() => Object.keys(JSON.parse(localStorage.getItem('ep3-shop'))).length) === 0, 'Alte Index-Häkchen werden aufgeräumt');
  const vis = async () => page.evaluate(() => { const p = [...document.querySelectorAll('.page')].filter(x => !x.hidden); return p.map(x => x.getAttribute('data-route')).join(','); });
  const cur = async () => page.evaluate(() => { const a = document.querySelector('.tabbar [aria-current="page"]'); return a && a.getAttribute('data-tab'); });
  ok(await vis() === 'heute', 'Start zeigt Heute');
  ok((await page.$$eval('#todayList .row', r => r.length)) === 4, 'Heute hat 4 Mahlzeiten');
  // Heute -> Rezept -> zurück
  await page.click('#todayList .row >> nth=1');
  await page.waitForTimeout(100);
  const r1 = await vis();
  ok(r1.startsWith('r/'), 'Tippen auf Mahlzeit öffnet Rezept (' + r1 + ')');
  ok(await cur() === 'heute', 'Tab bleibt Heute');
  ok((await page.textContent(`[data-route="${r1}"] .back-t`)) === 'Heute', 'Zurück heißt Heute');
  await page.click(`[data-route="${r1}"] .back`);
  await page.waitForTimeout(150);
  ok(await vis() === 'heute', 'Zurück führt zu Heute');
  // Rezepte-Tab, Segment, Filter
  await page.click('.tabbar [data-tab="rezepte"]');
  await page.click('#seg [data-cat="snacks"]');
  ok(await page.evaluate(() => location.hash) === '#rezepte/snacks', 'Segment schreibt #rezepte/snacks');
  ok(await page.evaluate(() => [...document.querySelectorAll('#pg-rezepte .cat')].filter(c => !c.hidden).map(c => c.dataset.cat).join()) === 'snacks', 'Nur Snacks sichtbar');
  await page.click('#pg-rezepte .cat[data-cat="snacks"] .chip[data-f="light"]');
  ok((await page.$$eval('#pg-rezepte .cat[data-cat="snacks"] .rrow:not(.hide)', r => r.length)) === 2, 'Filter Herzhaft zeigt 2');
  // Suche
  await page.fill('#q', 'reis');
  await page.waitForTimeout(50);
  const hits = await page.$$eval('#pg-rezepte .rrow', rs => rs.filter(r => r.offsetParent !== null).map(r => r.getAttribute('href')));
  ok(hits.includes('#r/m-burrito'), 'Suche "reis" findet die Burrito-Pfanne: ' + hits.join(' '));
  await page.fill('#q', 'zimt');
  const hits2 = await page.$$eval('#pg-rezepte .rrow', rs => rs.filter(r => r.offsetParent !== null).length);
  ok(hits2 >= 5, 'Suche "zimt" findet mehrere Rezepte (' + hits2 + ')');
  await page.fill('#q', 'xyzxyz');
  ok(await page.isVisible('#noRes'), 'Keine Treffer-Hinweis');
  await page.click('#qx');
  ok(await page.evaluate(() => [...document.querySelectorAll('#pg-rezepte .cat')].filter(c => !c.hidden).length) === 1, 'Suche geleert: eine Kategorie');
  // Rezept aus Liste, Schritte abhaken
  await page.click('#seg [data-cat="mittagessen"]');
  await page.evaluate(() => window.scrollTo(0, 400));
  await page.click('#pg-rezepte a[href="#r/m-maccheese"]');
  await page.waitForTimeout(100);
  ok(await vis() === 'r/m-maccheese', 'Mac & Cheese geöffnet');
  ok((await page.textContent('[data-route="r/m-maccheese"] .back-t')) === 'Rezepte', 'Zurück heißt Rezepte');
  await page.click('[data-route="r/m-maccheese"] li[data-step="m-maccheese:0"] .stepck');
  await page.click('[data-route="r/m-maccheese"] li[data-step="m-maccheese:2"] .stepck');
  ok((await page.textContent('[data-route="r/m-maccheese"] .sc')) === '2 von 5', 'Zähler 2 von 5');
  ok(await page.$eval('[data-route="r/m-maccheese"] li[data-step="m-maccheese:0"]', li => li.classList.contains('done') && getComputedStyle(li.querySelector('.st')).textDecorationLine.includes('line-through')), 'Schritt durchgestrichen');
  await page.goBack();
  await page.waitForTimeout(150);
  ok(await vis() === 'rezepte', 'Browser-Zurück führt zur Liste');
  const sy = await page.evaluate(() => window.scrollY);
  ok(sy > 300, 'Scrollposition der Liste wiederhergestellt (' + sy + ')');
  // Einkauf
  await page.click('.tabbar [data-tab="einkauf"]');
  for (const i of [0, 3, 7, 20]) await page.locator('label.ck').nth(i).click();
  ok((await page.textContent('#shopCount')) === '4 von 63', 'Einkauf 4 von 63');
  ok((await page.$$eval('.ck.done', x => x.length)) === 4, '4 Einträge durchgestrichen');
  await page.click('#hideDone');
  ok((await page.$$eval('.ck.done', x => x.filter(e => e.offsetParent !== null).length)) === 0, 'Erledigte ausgeblendet');
  // Theme
  await page.click('#pg-einkauf [data-theme-toggle]');
  const th = await page.evaluate(() => document.documentElement.getAttribute('data-theme'));
  // Reload: alles noch da?
  await page.reload();
  await page.waitForTimeout(150);
  ok(await vis() === 'einkauf', 'Reload bleibt auf Einkauf');
  ok((await page.textContent('#shopCount')) === '4 von 63', 'Einkauf nach Reload gespeichert');
  ok(await page.evaluate(() => document.getElementById('shopLists').classList.contains('hide-done')), 'Ausblenden gespeichert');
  ok(await page.evaluate(() => document.documentElement.getAttribute('data-theme')) === th, 'Theme gespeichert (' + th + ')');
  await page.click('#hideDone');
  await page.click('[data-reset="shop"]');
  ok((await page.textContent('#shopCount')) === '0 von 63', 'Zurücksetzen');
  // Schritte nach Reload + Ablauf
  await page.evaluate(() => { location.hash = 'r/m-maccheese'; });
  await page.waitForTimeout(100);
  ok((await page.textContent('[data-route="r/m-maccheese"] .sc')) === '2 von 5', 'Schritte nach Reload gespeichert');
  await page.evaluate(() => { const s = JSON.parse(localStorage.getItem('ep-steps')); s['m-maccheese:0'] = Date.now() - 2*3600*1000 - 1000; localStorage.setItem('ep-steps', JSON.stringify(s)); });
  await page.reload();
  await page.waitForTimeout(100);
  ok((await page.textContent('[data-route="r/m-maccheese"] .sc')) === '1 von 5', 'Abgelaufener Schritt nach 2 Std weg');
  // Alte Links
  for (const [h, want] of [['#m-cheeseburger', 'r/m-cheeseburger'], ['#lecker-ohne-salz', 'w/lecker-ohne-salz'], ['#einkauf', 'einkauf'], ['#abendessen', 'rezepte'], ['#woche', 'woche'], ['#x-schoko-quark-mousse-mit-beeren', 'r/x-schoko-quark-mousse-mit-beeren']]) {
    await page.evaluate(h => { location.hash = h; }, h);
    await page.waitForTimeout(80);
    ok(await vis() === want, `Link ${h} -> ${want}`);
  }
  ok(await page.evaluate(() => [...document.querySelectorAll('#pg-rezepte .cat')].filter(c => !c.hidden).map(c => c.dataset.cat).join()) !== '', 'Kategorie gesetzt');
  // Woche: Tag wählen
  await page.evaluate(() => { location.hash = 'woche'; });
  await page.click('#days .day[data-day="4"]');
  ok((await page.textContent('#daySum .sum-l')).includes('Freitag'), 'Woche: Freitag gewählt');
  ok((await page.$$eval('#dayList .row', r => r.length)) === 4, 'Woche: 4 Mahlzeiten');
  // Alle Rezept-Links in Heute/Woche zeigen auf existierende Seiten
  const bad = await page.evaluate(() => {
    const routes = new Set([...document.querySelectorAll('.page')].map(p => p.dataset.route));
    return [...document.querySelectorAll('a[href^="#r/"], a[href^="#w/"]')].map(a => a.getAttribute('href').slice(1)).filter(h => !routes.has(h));
  });
  ok(bad.length === 0, 'Alle internen Links gültig ' + bad.join(' '));
  ok(errs.length === 0, 'Keine JS-Fehler ' + errs.join(' | '));
  await browser.close();
  console.log(fails.length ? 'FEHLER:\n' + fails.join('\n') : 'ALLE TESTS OK');
})();
