# Ernährungsplan

Persönlicher Wochenplan (Deutsch) als eine einzige Datei: `index.html`, ohne externe Abhängigkeiten.

## Design – so beibehalten

Der Nutzer mag das Design von Wochenplan 5.0 (Commit `1a56677`) ausdrücklich. Alle Änderungen und neuen Seiten in genau diesem Stil bauen; auch bei neuen Projekten des Nutzers ist das der Wunschstil.

- **Stil:** modernes Apple-Design im Look von iOS 26: ruhig, viel Luft, große fette Titel, Glas-Elemente mit Unschärfe.
- **Aufbau:** Tabs Heute · Rezepte · Woche · Einkauf · Wissen. Handy: schwebende Glas-Tab-Leiste unten (Kapsel). Ab 1080 px: schwebende Glas-Seitenleiste links, aktiver Eintrag blau gefüllt.
- **Seiten:** großer Titel 34 px fett, darüber eine kleine graue Zeile in Großbuchstaben. Oben Glas-Knöpfe (Zurück, Hell/Dunkel); beim Scrollen erscheint der kleine Titel in der Leiste. Details öffnen als eigene Seite mit Zurück-Knopf.
- **Listen:** weiße Karten (Radius 22 px) auf `#f2f2f7`, Haarlinien, 48-px-Kacheln mit Emoji auf zartem Farbverlauf, farbige Kategorie-Zeile über dem Titel, grauer Chevron rechts.
- **Bedienelemente:** Segment-Umschalter als Kapsel mit weißem Daumen, Filter-Chips (aktiv schwarz/weiß invertiert), Suchfeld als graue Kapsel, runde grüne Häkchen wie in der Erinnerungen-App, Fortschrittsring.
- **Farben (Apple-Systemfarben):** Blau `#007aff` (dunkel `#0a84ff`), Grün `#34c759`, Rot `#ff3b30`. Kategorien: Frühstück Orange, Mittag Grün, Snack Türkis, Abend Indigo, Süßes Pink. Für farbigen Text die dunkleren Kontrastvarianten (z. B. `#c93400`, `#248a3d`).
- **Schrift:** System-Schrift (`-apple-system`, SF Pro), große Zahlen in `ui-rounded`, Zahlen tabellarisch.
- **Hell und Dunkel:** `data-theme` auf `<html>`; dunkel mit Grund `#000` und Karten `#1c1c1e`. Ohne gesetztes Thema (z. B. ohne JavaScript) folgt die Seite der Systemeinstellung; `build.py` spiegelt dafür alle `html[data-theme="dark"]`-Regeln in `@media (prefers-color-scheme: dark)`.
- **Bewegung:** dezent (Seitenwechsel 0,2 bis 0,4 s), `prefers-reduced-motion` beachten.
- **Referenz:** Das komplette CSS und JS steht in `index.html`. Für neue Seiten oder Projekte von dort übernehmen statt neu zu erfinden.

## Inhalte – Wochenplan 6.1

Die Rezepte wurden in 6.0 auf ausdrücklichen Wunsch komplett neu gemacht, weil die alten ohne Salz „tot“ geschmeckt haben (vor allem die Erdnuss-Nudeln und das trockene Haferflocken-Frühstück). In 6.1 wurde jedes Rezept auf Geschmack ohne Salz geprüft und nachgeschärft; die Caprese ist durch einen Feta-Dip ersetzt, die Joker-Pasta nimmt Feta statt Mozzarella light. Der Nutzer will nicht ständig ändern. Er isst gerne Nudeln, Reis, Käse und Burger und will einfache, schnelle, wirklich leckere Gerichte. Rezepte nur ändern, wenn der Nutzer darum bittet. Feste Vorgaben für jede Änderung:

- kein Salz zum Würzen, nirgends. Käse, Brot, Wraps, Senf und Thunfisch mit ihrem natürlichen Salzgehalt sind erlaubt und der wichtigste Geschmacksträger
- Geschmack zuerst: Käse (Parmesan, Feta, Gouda, Mozzarella), möglichst obendrauf; Feta als salzigsten Käse gezielt einsetzen. Senf als Würze (Rührei, Burger-Patty, Fisch-Panade). Fleisch und Pilze braun braten, Pilze nie roh auf die Pizza. Tomatenmark und Gewürze rösten, Säure zum Schluss
- Nudeln in der Soße fertig garen; den Reisbeutel 2 Minuten früher herausnehmen und den Reis in der Soße fertig garen oder in der Pfanne mit den Bratresten schwenken, nie pur servieren
- Cherry- oder Cocktailtomaten statt großer Tomaten, nicht in den Kühlschrank
- keine Gerichte, die von Salz oder Sojasauce leben (asiatische Soßen, Dal, schlichte Kartoffeln mit Quark)
- Frühstück cremig statt trocken: höchstens 50 g Haferflocken, mit Skyr und Milch
- Reis immer 125 g (Kochbeutel)
- Kartoffeln nur für Pommes in den Airfryer
- schnell nach der Uni: 10 bis 30 Minuten
- vollständige Zutatenlisten inklusive Gewürze und Kleinkram; jede Zutat steht auf der Einkaufsliste, und die Mengen reichen für den Wochenvorschlag
- gesund und fitnesstauglich: rund 2.000 bis 2.100 kcal und 140 g Protein am Tag; Kaufland, etwa 8 € pro Tag
- Süßes (6 Rezepte) stammt aus der vorigen Fassung; in 6.1 nur etwas mehr Honig in Schoko-Mousse und Zimtschnecken-Füllung, weil Kakao und Teig ohne Salz herber schmecken

## Technik

- `index.html` wird aus `src/` erzeugt, nicht von Hand bearbeiten: `cd src && python3 build.py plan_src.html mahlzeiten.html suesses.html style.css app.js ../index.html` (braucht `beautifulsoup4`). Rezepte, Wochenplan und Einkaufsliste stehen in `src/mahlzeiten.html`, Nährwerte werden aus `data-n` mit der Tabelle `NUT` in `src/build.py` berechnet.
- Test: `node src/test.js` (Playwright mit Chromium), prüft die Seite mit und ohne JavaScript.
- **Muss ohne JavaScript bedienbar bleiben.** Datei-Vorschauen auf iPhone, iPad und Mac (Dateien-App, Mail, Anhänge, Quick Look) führen kein JavaScript aus; daran ist 6.1 auf Apple-Geräten zuerst gescheitert. So funktioniert es:
  - Der Kopf setzt `class="js"` an `<html>`. Bricht `app.js` ab, fehlt `window.EP_OK`, und ein Sicherheitsnetz am Ende entfernt die Klasse wieder.
  - Ohne `js` gelten die Regeln „Ohne JavaScript“ am Ende von `style.css`: alle Seiten untereinander, ein Tipp auf einen Link zeigt per `:target` nur noch diese Seite. Jede Seite beginnt mit einem Sprungziel `<span class="anc" id="<route>">` (`anc()` in `build.py`).
  - `.jsonly` und `.nojs` markieren Inhalte für nur einen der beiden Modi. Heute und Woche haben fertig gerenderte Tageskarten (`sum_card`/`meal_rows` in `build.py`, gleiches Markup wie `sumCard`/`mealRows` in `app.js`; bei Änderungen beide anpassen).
  - Neue Navigation immer als `<a href="#route">` mit passendem Sprungziel bauen, nie nur als Knopf mit JavaScript.
- **Artifact zum Benutzen am iPhone** (mit JavaScript, Häkchen werden gespeichert): https://claude.ai/artifact/LWmkCskHiWvcjTbYZSf6E2, Titel „Mein Ernährungsplan“. Nach jeder Änderung an `index.html` neu veröffentlichen: `cd src && python3 artifact.py ../index.html <ziel.html>`, dann die Zieldatei mit dem Artifact-Tool und `url` auf diesen Link veröffentlichen, damit der Link gleich bleibt.
- Routen: `#heute`, `#rezepte/<kategorie>`, `#r/<rezept-id>`, `#woche`, `#einkauf`, `#wissen`, `#w/<artikel>`. Alte Links wie `#m-gyros` werden umgeleitet.
- `localStorage`: `ep-theme`, `ep3-shop` (Einkaufshäkchen, an den Namen der Einträge gebunden; Einträge, die nicht mehr auf der Liste stehen, werden beim Laden entfernt), `ep-steps` (Schritt-Häkchen, laufen nach 2 Stunden ab), `ep-shop-hide`. Nicht umbenennen, sonst gehen gespeicherte Häkchen verloren.
- Nach Änderungen prüfen: Handy (390 px) und Desktop (1440 px), hell und dunkel, kein horizontales Scrollen, keine JS-Fehler.
