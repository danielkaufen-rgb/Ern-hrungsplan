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
- **Hell und Dunkel:** `data-theme` auf `<html>`; dunkel mit Grund `#000` und Karten `#1c1c1e`.
- **Bewegung:** dezent (Seitenwechsel 0,2 bis 0,4 s), `prefers-reduced-motion` beachten.
- **Referenz:** Das komplette CSS und JS steht in `index.html`. Für neue Seiten oder Projekte von dort übernehmen statt neu zu erfinden.

## Inhalte – eingefroren

Die Rezepte gelten als fertig. Nicht ändern, außer der Nutzer bittet ausdrücklich darum (zum Beispiel, weil ein Gericht nach dem Kochen nicht schmeckt). Feste Vorgaben für jede Änderung:

- kein Salz, nirgends
- Reis immer 125 g (Kochbeutel)
- Kartoffeln nur für Pommes in den Airfryer, sonst gekocht oder gebraten und gewürzt
- schnell nach der Uni: 15 bis 25 Minuten
- vollständige Zutatenlisten inklusive Gewürze und Kleinkram; jede Zutat steht auf der Einkaufsliste
- günstig (Kaufland), gesund, rund 2.000 kcal und 140 g Protein am Tag

## Technik

- Routen: `#heute`, `#rezepte/<kategorie>`, `#r/<rezept-id>`, `#woche`, `#einkauf`, `#wissen`, `#w/<artikel>`. Alte Links wie `#m-gyros` werden umgeleitet.
- `localStorage`: `ep-theme`, `ep3-shop` (Einkaufshäkchen), `ep-steps` (Schritt-Häkchen, laufen nach 2 Stunden ab), `ep-shop-hide`. Nicht umbenennen, sonst gehen gespeicherte Häkchen verloren.
- Nach Änderungen prüfen: Handy (390 px) und Desktop (1440 px), hell und dunkel, kein horizontales Scrollen, keine JS-Fehler.
