"""Ernährungsplan, Wochenplan 6.4 (Datenteil).
Quellen: plan_src (Küchen-Grundlagen, Airfryer-Technik), mahlzeiten6.html (Rezepte, Woche, Einkauf), suesses4.html."""
import re, sys, html, json
from bs4 import BeautifulSoup

src, meals_path, sweet_path, css_path, js_path, out = sys.argv[1:7]
soup = BeautifulSoup(open(src, encoding="utf-8").read(), "html.parser")
msoup = BeautifulSoup(open(meals_path, encoding="utf-8").read(), "html.parser")
ssoup = BeautifulSoup(open(sweet_path, encoding="utf-8").read(), "html.parser")
CSS = open(css_path, encoding="utf-8").read()
# Hell/Dunkel nach Systemeinstellung, solange kein Thema gesetzt ist (z. B. ohne JavaScript):
# alle html[data-theme="dark"]-Regeln der obersten Ebene zusätzlich in prefers-color-scheme spiegeln
_dark = re.findall(r'(?m)^html\[data-theme="dark"\]([^{]*)\{([^}]*)\}', CSS)
CSS += ("\n@media (prefers-color-scheme: dark){\n"
        + "".join(f':root:not([data-theme="light"]){sel}{{{body}}}\n' for sel, body in _dark) + "}\n")
JS = open(js_path, encoding="utf-8").read()
E = html.escape

def section(title_start):
    for s in soup.find_all("section"):
        if s.h2 and s.h2.get_text().startswith(title_start):
            return s
    raise KeyError(title_start)

def inner(tag):
    return "".join(str(c) for c in tag.contents).strip()

def body_of_details(d):
    d.summary.decompose()
    return inner(d)

def slug(s):
    s = s.lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

NUT = {  # kcal, Protein je 100 g
 'HB':(105,23.5),'QK':(70,13),'HF':(372,13.5),'KAR':(70,2.0),'REIS':(350,7),'NUD':(355,12.5),'LIN':(340,24),
 'PAS':(30,1.3),'TM':(82,4.5),'KARO':(40,0.8),'ZW':(40,1.2),'TKG':(40,2.5),'THF':(108,25),'OEL':(900,0),
 'VKB':(215,7),'WK':(25,1.4),'GUR':(12,0.6),'TOM':(18,0.9),'PAP':(30,1.0),'PAN':(355,11),'STAE':(350,0.3),
 'HON':(305,0.4),'SENF':(100,6),'ZIT':(30,0.5),'KOK':(90,0.9),'EMUS':(600,25),'BEER':(40,1.0),'KAK':(350,20),'KICH':(340,19),
 'RH':(210,20),'SKY':(63,11),'MIL':(47,3.4),'PAR':(398,33),'MOZ':(160,19.5),'KAE':(360,25),'FETA':(265,16),'HUE':(100,12.5),
 'TOR':(310,8.5),'SEE':(75,17),'KID':(105,7.5),'MAIS':(85,2.8),'BRK':(34,3),'CHA':(22,3),'WAL':(690,15),'BUT':(740,0.7),
 'BAL':(90,0.5),'SPI':(20,2.5)}
NUT_ST = {'EI':(78,7),'BAN':(106,1.3),'APF':(72,0.6),'BRO':(138,5.4)}  # je Stück

def nutrition(spec):
    k = p = 0.0
    for part in spec.split(","):
        n, a = part.split(":"); a = float(a)
        if n in NUT_ST: k += NUT_ST[n][0] * a; p += NUT_ST[n][1] * a
        else: k += NUT[n][0] * a / 100; p += NUT[n][1] * a / 100
    return k, p

def num(s):
    """'35,1 g' / '1.984' -> float"""
    return float(re.sub(r"[^\d,]", "", s).replace(",", "."))

def de(x, dec=0):
    s = f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s

def rows_of(table):
    rows = []
    for tr in table.find_all("tr"):
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        if "total" in (tr.get("class") or []):
            continue
        rows.append(tds[:1] if "grp" in (tr.get("class") or []) else tds)
    return rows

def ing_table(rows):
    body = ""
    for r in rows:
        if len(r) == 1:
            body += f'<div class="ing-g">{E(r[0])}</div>'
            continue
        body += f'<div class="ing-r"><span class="nm">{E(r[0])}</span><span class="n">{E(r[1])}</span></div>'
    return f'<div class="ing c2">{body}</div>'

def recipe_item(r, kind_label, kind_cls, meta_chips, extra_attr=""):
    meta = " · ".join([kind_label] + [c for c in meta_chips if c])
    return f'''
<details class="recipe" id="{r["id"]}" {extra_attr}>
  <summary>
    <span class="thumb t-{kind_cls}"><span class="emo">{r["emo"]}</span></span>
    <span class="rmid"><span class="rname">{E(r["title"])}</span><span class="rmeta"><i class="d k-{kind_cls}"></i>{meta}</span></span>
    <span class="rnums"><span class="rk"><b class="num">{r["kcal"]}</b> <small>{r.get("unit", "kcal")}</small></span><span class="rp"><b class="num">{r["prot"]}</b> <small>Protein</small></span></span>
    <span class="chev">▾</span>
  </summary>
  <div class="rbody">
    {r.get("lead", "")}
    <div class="rcols">
      <div class="rcol-ing"><div class="colh">Zutaten</div>{ing_table(r["rows"])}</div>
      <div class="rcol-how"><div class="colh">Zubereitung</div><div class="howto">{r["body"]}</div></div>
    </div>
  </div>
</details>'''

# ---------- Frühstück, Mittag, Snack ----------
TYPE = {"meat": "Hähnchen", "fish": "Thunfisch", "veg": "Vegetarisch"}
meals = {"frueh": [], "mittag": [], "snack": []}
for v in msoup.select("div.v"):
    if v.get("data-from"):
        body = body_of_details(section(v["data-from"]).find("details"))
        body = body.replace('<li><b>Würzen.</b>', '<li><b>Würzen.</b>')  # unverändert übernommen
    else:
        body = inner(v.find("div", class_="body"))
    wz = v.find("div", class_="wuerz")
    r = dict(id=v["data-id"], slot=v["data-slot"], kind=v["data-kind"], emo=v["data-emo"], title=v.h3.get_text(strip=True),
             kcal=None, prot=None, time=v["data-time"], short=v["data-short"],
             light=v.get("data-light") == "1", kindlabel=v.get("data-kindlabel") or TYPE.get(v["data-kind"], ""),
             leadtxt=v.find("p", class_="lead").get_text(" ", strip=True), rows=rows_of(v.table), body=body)
    kc, pr = nutrition(v["data-n"])
    r["kcal"], r["prot"] = de(kc), de(pr, 1) + " g"
    r["lead"] = f'<p class="rlead">{E(r["leadtxt"])}</p>' + (f'<div class="wzgrid">{inner(wz)}</div>' if wz else "")
    meals[r["slot"]].append(r)
byid = {r["id"]: r for slot in meals.values() for r in slot}

def meal_list(slot):
    out_ = ""
    for r in meals[slot]:
        chips = [r["time"]] + (["leichter Snack"] if r["light"] else [])
        out_ += recipe_item(r, r["kindlabel"], r["kind"], chips, f'data-kind="{r["kind"]}"')
    return out_

lunch_html, frueh_html = meal_list("mittag"), meal_list("frueh")
lunches = meals["mittag"]
n_meat = sum(l["kind"] == "meat" for l in lunches)
n_fish = sum(l["kind"] == "fish" for l in lunches)
n_veg = sum(l["kind"] == "veg" for l in lunches)
lk = [num(l["kcal"]) for l in lunches]

# ---------- Snacks ----------
snacks = meals["snack"]
snack_html = meal_list("snack")
n_sweet_snacks = sum(x["kind"] == "snack" for x in snacks)
sk = [num(x["kcal"]) for x in snacks]

# ---------- Süßes (unverändert) ----------
SWEET_KIND = {"pan": "Pfanne", "air": "Airfryer", "cold": "Kalt"}
sweet_sub = ssoup.find("p", class_="sub").get_text(" ", strip=True)
sweet_rule = ssoup.find("p", class_="rule").get_text(" ", strip=True)
sweets = []
for v in ssoup.select("div.v.sweet"):
    title = v.h3.get_text(strip=True)
    per = v.get("data-per", "")
    sweets.append(dict(id="x-" + slug(title), title=title, kind=v["data-kind"], emo=v["data-emo"],
                       kcal=v["data-kcal"], prot=v["data-prot"], price=v["data-price"], time=v["data-time"],
                       yld=v["data-yield"], per=per, fit=v["data-fit"], rows=rows_of(v.table),
                       unit="kcal/Stück" if per else "kcal", body=body_of_details(v.details)))
sweet_html = ""
for x in sweets:
    per = f" {x['per']}" if x["per"] else ""
    short_time = x["time"].split(",")[0].replace(" plus ", " + ")
    x["lead"] = (f'<p class="rlead">{x["kcal"]} kcal · {x["prot"]} Protein · {x["price"]}{per} · {E(x["yld"])} · {E(x["time"])}</p>'
                 f'<p class="fit"><b>So passt es in den Plan:</b> {E(x["fit"])}</p>')
    sweet_html += recipe_item(x, SWEET_KIND[x["kind"]], x["kind"], [E(x["yld"]), E(short_time)], f'data-kind="{x["kind"]}"')
n_pan = sum(x["kind"] == "pan" for x in sweets)
n_air = sum(x["kind"] == "air" for x in sweets)
n_cold = sum(x["kind"] == "cold" for x in sweets)
sweet_shop = [[td.get_text(strip=True) for td in tr.find_all("td")] for tr in ssoup.find("table", class_="sweetshop").find_all("tr")
              if "total" not in (tr.get("class") or []) and not any(w in tr.get_text().lower() for w in ("honig", "beeren", "kakao", "vanille"))]
sweet_shopnote = inner(ssoup.find("p", class_="shopnote"))

# ---------- Woche (Summen werden aus den Rezepten berechnet) ----------
DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
week, week_html = [], ""
for tr in msoup.find("table", class_="week").find_all("tr"):
    d, *ids = [td.get_text(strip=True) for td in tr.find_all("td")]
    items = [byid[i] for i in ids]
    k = sum(num(x["kcal"]) for x in items)
    p = sum(num(x["prot"]) for x in items)
    week.append(dict(d=d, k=de(k), p=de(p, 1) + " g", meals=[[x["short"], x["id"], x["emo"]] for x in items]))
    links = "".join(f'<a class="wkx" href="#{x["id"]}" data-open="{x["id"]}"><i>{x["emo"]}</i><span>{E(x["short"])}</span></a>' for x in items)
    week_html += f'''<div class="wk" data-day="{DAYS.index(d)}"><span class="wkd">{d}</span><div class="wkmeals">{links}</div>
  <span class="wkn num">{de(k)}</span><span class="wkn num wkp">{de(p, 1)} g</span></div>'''
_sl = [[byid[i] for i in col] for col in zip(*[[td.get_text(strip=True) for td in tr.find_all("td")][1:]
                                               for tr in msoup.find("table", class_="week").find_all("tr")])]
slot_avg = [(sum(num(x["kcal"]) for x in L) / len(L), sum(num(x["prot"]) for x in L) / len(L)) for L in _sl]
_tot = sum(k for k, _ in slot_avg)
bar_w = [f"{k / _tot * 100:.1f}%" for k, _ in slot_avg]
def r10(x): return de(round(x / 10) * 10)
SA = [(f"~{r10(k)}", f"~{de(p)} g") for k, p in slot_avg]
wk_k = [num(w["k"]) for w in week]
wk_p = [num(w["p"]) for w in week]
avg_k, avg_p = sum(wk_k) / 7, sum(wk_p) / 7
week_note = (f'Ohne Abendessen liegt jeder Tag zwischen {de(min(wk_k))} und {de(max(wk_k))} kcal und zwischen {de(min(wk_p))} und {de(max(wk_p))} g Protein, '
             f'im Schnitt {de(avg_k)} kcal und {de(avg_p)} g. Die Tomaten-Feta-Pasta ist der Joker, wenn du ein Mittagessen tauschen willst. '
             '<strong>Zeitspar-Kombis:</strong> Die Bolognese am Montag doppelt kochen, dann ist der Dienstag in 10 Minuten erledigt. '
             'Montag und Dienstag gibt es warmes Porridge, die Overnight Oats für Donnerstag und Freitag setzt du am Mittwochabend an. '
             'Was von Champignons, Feta, Gouda, Brot und Bohnen übrig bleibt, frierst du ein. Bei jedem Eintrag der Einkaufsliste steht, wie lange er reicht. '
             '<strong>Wichtig:</strong> Hähnchen und Hack gleich nach dem Einkauf in Portionen einfrieren, was du nicht in den nächsten 1 bis 2 Tagen brauchst, '
             'und am Vorabend zum Auftauen in den Kühlschrank legen.')

# ---------- Einkauf ----------
groups, cur = [], None
for tr in msoup.find("table", class_="shop").find_all("tr"):
    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
    if "grp" in (tr.get("class") or []):
        cur = dict(name=tds[0], note=tds[1], items=[])
        groups.append(cur)
    else:
        cur["items"].append(tds)
groups.append(dict(name="Für Süßes", note="Nur wenn du aus „Süßes“ backst, plus 1 bis 2 extra reife Bananen und Äpfel. Eier, Honig, Beeren, Kakao und Vanille stehen schon oben", items=sweet_shop, optional=True))

def price(s):
    return num(s)

shop_html, idx = "", 0
for g in groups:
    total = sum(price(it[-1]) for it in g["items"])
    g["total"] = total
    shop_html += f'<div class="ckgroup"><span><b>{E(g["name"])}</b><small>{E(g["note"])}</small></span><span class="num">{de(total, 2)} €</span></div>'
    for it in g["items"]:
        shop_html += (f'<label class="ck"><input type="checkbox" data-key="shop" data-i="{idx}"><span class="box"></span>'
                      f'<span class="cknm">{E(it[0])}<small>{E(it[1])}</small></span><span class="ckp num">{E(it[-1])}</span></label>')
        idx += 1
n_shop = idx
first_buy = sum(g["total"] for g in groups if not g.get("optional"))
weekly = groups[0]["total"]

# ---------- Wissen ----------
def info_section(title_start):
    s = section(title_start)
    sub = s.find("p", class_="sub").get_text(" ", strip=True)
    body = s.find("div", class_="panel") or s.find("div", class_="callout")
    for t in body.find_all("table"):
        t["class"] = (t.get("class") or []) + ["tbl"]
        t.wrap(soup.new_tag("div", attrs={"class": "tblwrap"}))
    for h in body.find_all("h3", class_="mini"):
        h["class"] = ["subhead"]
        if h.has_attr("style"):
            del h["style"]
    for td in body.find_all("td", class_=["ok", "warn"]):
        cls, txt = td["class"][0], td.get_text(strip=True)
        td.clear()
        span = soup.new_tag("span", attrs={"class": f"pill {cls}"})
        span.string = txt
        td.append(span)
        del td["class"]
    return sub, inner(body), "callout" in (body.get("class") or [])

ehrlich = ("Was an den alten Rezepten schiefging und was diese Fassung anders macht.",
 '<p><strong>Die alten Rezepte waren auf Nährwerte gebaut, nicht auf Geschmack.</strong> Quark mit Wasser, viele Haferflocken, Nudeln aus ungesalzenem Wasser. Das ist gesund, aber man isst es nicht gern, und dann hält man keinen Plan durch.</p>'
 '<p><strong>Ohne Salz wird es nur mit Käse und Röstaromen richtig lecker.</strong> Darum gibt es jetzt Bolognese mit Parmesan, Mac &amp; Cheese, Cheeseburger, zwei Burritos und Gyros mit Feta. Das sind Gerichte, die von sich aus herzhaft sind.</p>'
 '<p><strong>Gerichte, die Salz brauchen, sind raus.</strong> Erdnuss-Nudeln leben von Sojasauce, Curry und Dal von viel Salz. Ohne das schmecken sie flach, egal wie viel Zitrone dran ist.</p>'
 '<p><strong>Das Frühstück war zu trocken.</strong> 75 g Haferflocken mit Quark und Wasser sind ein Klumpen. Jetzt sind es 50 g mit Skyr und Milch, über Nacht eingeweicht oder warm als Porridge, am Wochenende gibt es Eier.</p>'
 '<p><strong>Käse und Fleisch kosten etwas.</strong> Käse, Rinderhack, Hähnchen und Skyr sind die teuersten Posten im Einkauf. Das ist der Preis für Essen, das man gerne isst.</p>'
 '<p><strong>Gib ihm zwei bis drei Wochen.</strong> Dein Geschmack gewöhnt sich an weniger Salz. Wenn ein Gericht dann immer noch nicht schmeckt, fliegt es raus.</p>',
 True)
def rng(vals, dec=0, unit=""):
    lo, hi = min(vals), max(vals)
    return f"{de(lo, dec)}–{de(hi, dec)}{unit}" if round(lo, dec) != round(hi, dec) else f"{de(lo, dec)}{unit}"
_slots = [("Frühstück", f'{len(meals["frueh"])} Varianten', "morgens", meals["frueh"]), ("Mittagessen", f'{len(meals["mittag"])} Varianten', "mittags", meals["mittag"]),
          ("Snack", f"{len(snacks)} Varianten", "nachmittags", snacks)]
_rows = "".join(f'<tr><td><strong>{n}</strong>, {v}</td><td>{w}</td><td class="n">{rng([num(x["kcal"]) for x in L])}</td>'
                f'<td class="n">{rng([num(x["prot"]) for x in L], 0, " g")}</td></tr>' for n, v, w, L in _slots)
tag_sub = "Drei Slots, jeder mit Auswahl. Die Varianten in einem Slot haben ähnlich viele Kalorien, deshalb kannst du tauschen, ohne nachzurechnen."
tag_html = (f'<div class="tblwrap"><table class="tbl"><thead><tr><th>Slot</th><th>Wann</th><th class="n">kcal</th><th class="n">Protein</th></tr></thead>'
            f'<tbody>{_rows}<tr class="total"><td>Tag im Wochenvorschlag, ohne Abendessen</td><td></td><td class="n">{rng(wk_k)}</td><td class="n">{rng(wk_p, 0, " g")}</td></tr></tbody></table></div>'
            '<p class="note">Die beiden Reisgerichte liegen wegen der 125 g Reis höher als die anderen Mittagessen. Wer sich an den Wochenvorschlag hält, muss nichts rechnen. '
            f'<strong>Das Abendessen gehört nicht zum Plan.</strong> Frühstück, Mittag und Snack bringen im Schnitt {de(avg_k)} kcal und {de(avg_p)} g Protein, alles Weitere kommt mit dem Abendessen dazu.</p>')

LECKER = (
 '<p class="lead-p">Die Erdnuss-Nudeln haben es gezeigt: Gesunde Zutaten allein schmecken ohne Salz tot. Jedes Rezept ist jetzt auf das gebaut, was Salz am besten ersetzt.</p>'
 '<h3 class="subhead">Warum es vorher tot geschmeckt hat</h3>'
 '<ul class="tricks">'
 '<li><b>Nudeln aus ungesalzenem Wasser.</b> Normalerweise holen sich Nudeln ihren Geschmack aus dem Salzwasser. Ohne Salz müssen sie ihn aus der Soße holen. Deshalb garen sie jetzt die letzten 2 Minuten in der Soße.</li>'
 '<li><b>Soßen, die Salz brauchen.</b> Erdnusssoße ohne Sojasauce und Dal ohne Salz bleiben flach, egal wie viel Zitrone dran ist. Solche Gerichte sind komplett raus.</li>'
 '<li><b>Zu wenig Käse und Umami.</b> Käse, braun gebratenes Fleisch, geröstetes Tomatenmark und Pilze schmecken von sich aus herzhaft. Davon gab es zu wenig.</li>'
 '<li><b>Zu viel Wasser, zu wenig Fett.</b> Quark mit Wasser und Haferflocken mit Wasser schmecken trocken und leer. Jetzt gibt es Skyr, Milch, Butter und Olivenöl in vernünftigen Mengen.</li>'
 '</ul>'
 '<h3 class="subhead">Die 7 Regeln für jedes Rezept</h3>'
 '<ol class="rules">'
 '<li><b>Käse ist dein Salz.</b> Parmesan, Feta und Gouda bringen ihre Würze von Natur aus mit, Feta am meisten. Ein Esslöffel frisch geriebener Parmesan macht mehr aus einem Gericht als jedes Gewürz. Am stärksten wirkt Käse obendrauf, weil er dort zuerst auf die Zunge trifft.</li>'
 '<li><b>Braun braten.</b> Hack und Hähnchen in die heiße Pfanne und 2 bis 3 Minuten nicht anfassen. Die braune Kruste ist der Geschmack. Pilze genauso: erst braun braten, dann weiterkochen.</li>'
 '<li><b>Nudeln und Reis in der Soße fertig machen.</b> Nudeln 2 Minuten früher abgießen und in der Soße fertig garen. Den Reisbeutel 2 Minuten früher herausnehmen und den Reis in der Soße fertig garen oder in der Pfanne mit den Bratresten schwenken, nie pur auf den Teller.</li>'
 '<li><b>Tomatenmark und Gewürze rösten.</b> 1 Minute in heißem Öl, bevor Flüssigkeit dazukommt. Kreuzkümmel, Rauchpaprika und Oregano schmecken dann voll statt staubig.</li>'
 '<li><b>Säure zum Schluss.</b> Zitrone, Balsamico, Senf oder schnelle Essiggurken. Säure macht Essen frisch und würzig, ohne dass es sauer schmeckt.</li>'
 '<li><b>Cremig und knusprig.</b> Geschmolzener Käse, Skyr-Dips, knusprige Pommes, gerösteter Hafer: Jedes Gericht hat etwas Cremiges und etwas mit Biss.</li>'
 '<li><b>Tomaten mit Geschmack.</b> Cherry- oder Cocktailtomaten statt großer Tomaten, und nie in den Kühlschrank. Große Tomaten schmecken im Herbst und Winter wässrig, und Kälte nimmt jeder Tomate Aroma. Ohne Salz merkst du das sofort.</li>'
 '</ol>'
 '<h3 class="subhead">Abschmeck-Check vor dem Servieren</h3>'
 '<div class="tblwrap"><table class="tbl"><thead><tr><th>Schmeckt …</th><th>Dann …</th></tr></thead><tbody>'
 '<tr><td><strong>fad, nach wenig</strong></td><td>Parmesan frisch drüberreiben, ein Spritzer Zitrone, frisch gemahlener Pfeffer</td></tr>'
 '<tr><td><strong>flach, irgendwie leer</strong></td><td>mehr braune Kruste, Tomatenmark anrösten, ein paar Tropfen Balsamico</td></tr>'
 '<tr><td><strong>zu sauer</strong></td><td>½ Teelöffel Honig oder etwas Käse</td></tr>'
 '<tr><td><strong>eintönig</strong></td><td>Chili, Kräuter, schnelle Essiggurken, etwas Knuspriges</td></tr>'
 '<tr><td><strong>trocken</strong></td><td>3 Esslöffel Nudelwasser, ein Skyr-Dip oder bei den Oats ein Schuss Milch</td></tr>'
 '</tbody></table></div>'
 '<h3 class="subhead">Dein Geschmack gewöhnt sich um</h3>'
 '<p class="note">Wer lange gesalzen gegessen hat, empfindet Essen ohne Salz die ersten Wochen als fad. Das liegt nicht an dir. Studien zu salzarmer Ernährung zeigen, dass sich der Geschmack nach etwa 2 bis 3 Monaten verschiebt. Dann schmeckt dir weniger Salz schon würzig, und stark gesalzenes Essen kommt dir zu salzig vor.</p>'
 '<h3 class="subhead">Ehrlich zu Käse und Salz</h3>'
 '<p class="note">Du gibst nirgends Salz dazu. Käse, Brot, Wraps und Senf enthalten aber von Natur aus oder vom Hersteller etwas Salz. Nach grober Rechnung bringen Frühstück, Mittag und Snack etwa 3 bis 4 g am Tag, dazu kommt dein Abendessen. '
 'Der Richtwert liegt bei 6 g, die meisten in Deutschland essen deutlich mehr. Falls du aus medizinischen Gründen auf Salz verzichtest, sprich die Käsemengen kurz mit deiner Ärztin oder deinem Arzt ab.</p>')

kueche = info_section("Küchen")
airfryer = info_section("Airfryer")
vitamine = ("Ehrliche Bilanz für Frühstück, Mittag und Snack, also ohne dein Abendessen. Calcium, Vitamin C und B12 sind gedeckt, vieles andere zu etwa drei Vierteln, bei Jod und Vitamin D musst du nachhelfen.",
 '<p class="note">Der Plan bringt etwa drei Viertel der Kalorien eines ganzen Tages, deshalb ist vieles nur zu etwa drei Vierteln gedeckt. Wo es knapp ist, steht dabei, was abends am meisten hilft.</p>'
 '<div class="tblwrap"><table class="tbl"><thead><tr><th>Nährstoff</th><th>Stand</th><th>Woher im Plan</th></tr></thead><tbody>'
 '<tr><td>Vitamin C</td><td><span class="pill ok">gedeckt</span></td><td>Paprika, Tomaten, Brokkoli, Zitronen, Beeren und Kartoffeln</td></tr>'
 '<tr><td>Calcium</td><td><span class="pill ok">gedeckt</span></td><td>Käse, Skyr und Milch bringen im Schnitt rund 1.000 mg am Tag</td></tr>'
 '<tr><td>Vitamin B12</td><td><span class="pill ok">gedeckt</span></td><td>Rindfleisch, Eier, Käse, Skyr und Milch, zusammen etwas über dem Bedarf</td></tr>'
 '<tr><td>Vitamin A</td><td><span class="pill warn">knapp</span></td><td>Karotten, rote Paprika und Brokkoli, dazu Käse, Eier und Butter, zusammen knapp neun Zehntel. Fix: abends Gemüse wie Karotten, Paprika oder Spinat</td></tr>'
 '<tr><td>B-Vitamine gesamt</td><td><span class="pill warn">knapp</span></td><td>Haferflocken, Vollkornbrot, Hähnchen, Rindfleisch und Milchprodukte bringen den Großteil, am knappsten ist Vitamin B1. Fix: abends Vollkorn, Hülsenfrüchte oder Fleisch</td></tr>'
 '<tr><td>Folat</td><td><span class="pill warn">knapp</span></td><td>Tomaten, Paprika, Vollkornbrot, Eier, Brokkoli, Bohnen und Linsen bringen gut drei Viertel. Fix: abends grünes Gemüse oder Salat</td></tr>'
 '<tr><td>Eisen und Zink</td><td><span class="pill warn">knapp</span></td><td>Rindfleisch, Haferflocken, Vollkornbrot, Eier, Käse, Bohnen und Linsen bringen grob drei Viertel bis den ganzen Bedarf. Die Säure aus Tomaten und Zitrone verbessert die Aufnahme. Fix: abends Fleisch, Hülsenfrüchte oder Vollkorn mit etwas Gemüse</td></tr>'
 '<tr><td>Kalium und Magnesium</td><td><span class="pill warn">knapp</span></td><td>Bananen, Kartoffeln, Haferflocken, Nüsse, Bohnen und Milchprodukte: Magnesium ist fast gedeckt, Kalium zu etwa drei Vierteln. Fix: abends Gemüse, Kartoffeln oder Hülsenfrüchte</td></tr>'
 '<tr><td>Ballaststoffe</td><td><span class="pill warn">knapp</span></td><td>rund 23 g am Tag aus Haferflocken, Vollkornbrot, Bohnen, Linsen, Gemüse und Obst, empfohlen sind 30 g. Fix: abends Vollkornbrot, Gemüse oder Hülsenfrüchte</td></tr>'
 '<tr><td><strong>Vitamin E</strong></td><td><span class="pill warn">knapp</span></td><td>Rapsöl, Paprika, Tomaten, Eier und Erdnussmus bringen etwa die Hälfte. Fix: 1 Esslöffel Sonnenblumenkerne oder gehackte Mandeln über die Oats</td></tr>'
 '<tr><td><strong>Jod</strong></td><td><span class="pill warn">Lücke</span></td><td>Ohne Jodsalz und ohne Seefisch die größte Lücke im Plan. Milch, Skyr, Käse und Eier bringen grob ein Drittel des Bedarfs. Fix: ein Jodpräparat, vorher mit Ärztin oder Arzt absprechen, oder ab und zu eine Portion Seelachs</td></tr>'
 '<tr><td><strong>Omega-3</strong></td><td><span class="pill warn">knapp</span></td><td>Die Walnüsse im Frühstück liefern pflanzliches Omega-3. Fix: ab und zu eine Portion Lachs, zum Beispiel 12 Minuten bei 200 °C im Airfryer</td></tr>'
 '<tr><td><strong>Vitamin D</strong></td><td><span class="pill warn">Lücke</span></td><td>Nicht über Essen lösbar, gilt in Deutschland von Oktober bis März für fast alle. Ein Präparat mit 1.000 IE kostet unter 5 € für sechs Monate</td></tr>'
 '</tbody></table></div>'
 '<p class="note">Unterm Strich: Ein Abendessen mit Gemüse, Vollkorn oder Hülsenfrüchten und etwas Fleisch oder Fisch schließt fast alle Lücken. Jod und Vitamin D behältst du trotzdem im Blick.</p>')
footer = ("Nährwerte gerundet, berechnet auf Basis von Standardwerten für rohe Zutaten. Abweichungen von drei bis fünf Prozent sind normal und für deine Zielwerte ohne Bedeutung. "
          "Kartoffeln wiegst du mit Schale, sie kommen nur als Pommes in den Airfryer. Herdstufen beziehen sich auf eine 9er-Skala bei Ceran oder Gas, bei Induktion jeweils eine Stufe weniger. "
          "Der Plan ist auf einen gesunden Erwachsenen mit normalem Aktivitätsniveau ausgelegt. Wenn du länger als ein paar Monate so isst oder Vorerkrankungen hast, lohnt sich einmal der Blick "
          "einer Ärztin oder eines Ernährungsberaters, vor allem wegen Jod und Vitamin D.")

SCHNELL = ('<ul class="tricks">'
  '<li><b>Wasserkocher statt Herd.</b> Wasser für Nudeln und Reis immer im Wasserkocher vorkochen. 3 statt 10 Minuten, bis es kocht.</li>'
  '<li><b>Einmal kochen, zweimal essen.</b> Die Bolognese am Montag doppelt kochen. Am Dienstag nur Nudeln kochen und die Soße 5 Minuten aufwärmen.</li>'
  '<li><b>Frühstück am Vorabend.</b> Overnight Oats für zwei Tage auf einmal ansetzen, das dauert 5 Minuten.</li>'
  '<li><b>Tiefkühlgemüse ohne Schneiden.</b> Brokkoli kocht einfach mit den Nudeln mit, Mais kommt gefroren in die Pfanne.</li>'
  '<li><b>Ein Topf, eine Pfanne.</b> Spiegelei, Rührei und der Hähnchen-Burrito brauchen nur eine Pfanne, das Porridge nur einen Topf, Mac &amp; Cheese Topf und Pfanne.</li>'
  '<li><b>Der Airfryer arbeitet nebenher.</b> Während die Pommes laufen, machst du Patty, Zwiebeln und Sauce. Dann ist alles gleichzeitig fertig.</li>'
  '<li><b>Fleisch portionsweise einfrieren.</b> Hähnchen und Hack gleich nach dem Einkauf in Portionen von 80 bis 125 g einfrieren und am Vorabend in den Kühlschrank legen. Dann musst du nur noch schneiden.</li>'
  '</ul>')

def info_card(icon, title, sub_, content, is_callout=False):
    cls = "callout" if is_callout else "prose"
    return f'''
<details class="card sec" id="{slug(title)}">
  <summary><span class="sico">{icon}</span><span class="shd"><span class="ctitle">{title}</span><span class="csub">{E(sub_)}</span></span><span class="chev">▾</span></summary>
  <div class="cbody"><div class="{cls}">{content}</div></div>
</details>'''

def slot_row(dot, name, kcal, prot, target):
    return (f'<a class="hl" href="#{target}" data-open="{target}"><span class="hn"><i class="{dot}"></i>{name}</span>'
            f'<span class="hv num">{kcal} <small>kcal</small></span><span class="hp num">{prot} Protein</span></a>')

fk = [num(r["kcal"]) for r in meals["frueh"]]
VORRAT_PRO_WOCHE = 13.50  # geschätzter Verbrauch aus Vorrat und Gewürzen pro Woche
cost_week = weekly + VORRAT_PRO_WOCHE
cost_day = round(cost_week / 7, 1)
COST_WEEK_S, COST_DAY_S = de(cost_week), de(cost_day, 2)
shop_note = (f'<p class="note"><strong>Beim ersten Einkauf rund {de(first_buy)} €,</strong> weil Vorrat und Gewürze dabei sind. '
             f'Danach kaufst du jede Woche nur „Jede Woche frisch“ für etwa {de(weekly)} € und vom Vorrat, was leer ist. '
             f'<strong>Echte Kosten: etwa {COST_WEEK_S} € pro Woche, also rund {COST_DAY_S} € am Tag,</strong> für Frühstück, Mittag und Snack. '
             'Das meiste Geld steckt in Käse, Fleisch und Skyr, also genau in dem, was den Geschmack und das Protein bringt.</p>'
             '<p class="note"><strong>Frisch halten:</strong> Hähnchen und Hack gleich nach dem Einkauf in Portionen einfrieren, was du nicht in den nächsten 1 bis 2 Tagen brauchst. '
             'Was du nicht in 4 Tagen aufbrauchst, frierst du ein: Bohnen, passierte Tomaten, Champignons, Feta, Gouda, Brot, Wraps und Brötchen. Bei jedem Eintrag steht, wie lange er reicht.</p>'
             '<p class="note"><strong>Zwei echte Sparhebel:</strong> Hähnchen und Hack nur im Angebot kaufen und einfrieren. '
             'Und Skyr gibt es oft im Angebot, ungeöffnet hält er mehrere Wochen.</p>')

# ======================= Oberfläche im Apple-Stil (Wochenplan 6.4) =======================
# Wird an den Datenteil (build6_data.py) angehängt. Rezepte, Mengen und Texte kommen aus den Quellen.
from collections import defaultdict

VERSION = "Wochenplan 6.4"
ICON_B64 = open("icon180.b64").read().strip()
kueche = (kueche[0].replace("jede Anleitung weiter unten", "jede Anleitung in den Rezepten"), kueche[1], kueche[2])

SVGS = {
 "chev": '<svg class="chev" viewBox="0 0 8 14" aria-hidden="true"><path d="M1.6 1.6 6.4 7l-4.8 5.4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "back": '<svg class="ico-back" viewBox="0 0 12 20" aria-hidden="true"><path d="M9.5 2.5 2.5 10l7 7.5" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "check": '<svg class="ico-check" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.6 8.6 6.6 11.5 12.4 4.6" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "search": '<svg class="ico-search" viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.6" cy="8.6" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="m13.2 13.2 4.3 4.3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 "moon": '<svg class="ico-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20.2 14.6A8.4 8.4 0 0 1 9.4 3.8a8.4 8.4 0 1 0 10.8 10.8Z" fill="currentColor"/></svg>',
 "sun": '<svg class="ico-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.4" fill="currentColor"/><path d="M12 2.6v2.3M12 19.1v2.3M2.6 12h2.3M19.1 12h2.3M5.35 5.35 7 7M17 17l1.65 1.65M5.35 18.65 7 17M17 7l1.65-1.65" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 "cal": '<svg class="ico-cal" viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15.5" rx="3.4" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M3.5 9.9h17M8 3v3.6M16 3v3.6" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>',
 "flame": '<svg class="ico-flame" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2.8c.6 3.3-1.8 5-3.4 7.1-1.2 1.6-1.9 3.1-1.9 4.9a5.3 5.3 0 0 0 10.6 0c0-2.3-1.1-3.9-2.2-5.2.1 1.6-.6 2.8-1.7 3.3.4-3.6-.9-7.6-1.4-10.1Z" fill="currentColor"/></svg>',
 "screen": '<svg class="ico-screen" viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="2.5" width="11" height="19" rx="2.8" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M12 7.2v4.1M10.2 9.2 12 7.2l1.8 2" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>',
}
TAB_ICONS = {
 "heute": '<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.5" fill="currentColor"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.55 1.55M17.15 17.15l1.55 1.55M5.3 18.7l1.55-1.55M17.15 6.85l1.55-1.55" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 "rezepte": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M5.5 3v5.4a2.75 2.75 0 0 0 5.5 0V3M8.25 3v5.4M8.25 11.2V21"/><path d="M18.3 21V3.2c-2.4.9-3.7 3.5-3.7 7v2.4c0 .9.7 1.5 1.6 1.5h2.1" fill="currentColor" fill-opacity=".18"/></svg>',
 "woche": '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3.5" y="5" width="17" height="15.5" rx="3.4" fill="currentColor" fill-opacity=".14" stroke="currentColor" stroke-width="1.9"/><path d="M3.5 9.9h17M8 3v3.6M16 3v3.6" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/><g fill="currentColor"><circle cx="8.2" cy="13.6" r="1.15"/><circle cx="12" cy="13.6" r="1.15"/><circle cx="15.8" cy="13.6" r="1.15"/><circle cx="8.2" cy="17.1" r="1.15"/><circle cx="12" cy="17.1" r="1.15"/></g></svg>',
 "einkauf": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="M2.6 3.6h2.5l2.3 11a1.7 1.7 0 0 0 1.7 1.4h8.4a1.7 1.7 0 0 0 1.7-1.3L21 7.3H6.1" fill="currentColor" fill-opacity=".14"/><circle cx="9.6" cy="20" r="1.35" fill="currentColor" stroke="none"/><circle cx="17.4" cy="20" r="1.35" fill="currentColor" stroke="none"/></svg>',
 "wissen": '<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"><path d="M12 6.6C10.2 5.1 7.6 4.4 3.4 4.6v14.1c4.2-.2 6.8.5 8.6 2 1.8-1.5 4.4-2.2 8.6-2V4.6c-4.2-.2-6.8.5-8.6 2Z" fill="currentColor" fill-opacity=".14"/><path d="M12 6.6v14"/></svg>',
}
TABS = [("heute", "Heute"), ("rezepte", "Rezepte"), ("woche", "Woche"), ("einkauf", "Einkauf"), ("wissen", "Wissen")]
DAYN = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

def join_de(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " und " + xs[-1]

def short_time(t):
    return t.split(",")[0].replace(" plus ", " + ")

BACK_TO = {"rezepte": "Rezepte", "wissen": "Wissen"}

def nav(title, back=None, right=""):
    # back: Tab, zu dem der Zurück-Knopf ohne JavaScript führt; app.js setzt Ziel und Text beim Anzeigen neu
    left = (f'<a class="nbtn back" href="#{back}" data-back aria-label="Zurück zu {BACK_TO[back]}">{SVGS["back"]}'
            f'<span class="back-t lbl">{BACK_TO[back]}</span></a>' if back else "")
    return (f'<header class="nav"><div class="nav-in"><div class="nav-l">{left}</div>'
            f'<div class="nav-t" aria-hidden="true">{E(title)}</div><div class="nav-r">{right}</div></div></header>')

THEME_BTN = (f'<button class="nbtn round" type="button" data-theme-toggle aria-label="Hell oder Dunkel umschalten">'
             f'{SVGS["moon"]}{SVGS["sun"]}</button>')
WAKE_BTN = (f'<button class="nbtn wake" type="button" aria-pressed="false" aria-label="Kochmodus: Bildschirm bleibt an" hidden>{SVGS["screen"]}<span class="lbl">Kochmodus</span></button>')

def anc(route):
    """Sprungziel mit der Route als id: Ohne JavaScript zeigt das CSS per :target die Seite, die es enthält."""
    return f'<span class="anc" id="{route}"></span>'

def tile(emo, color, cls=""):
    return f'<span class="tile t-{color} {cls}" aria-hidden="true">{emo}</span>'

def row_link(href, emo, color, title, sub="", cap="", cap_color=None, extra_attr=""):
    cap_html = f'<span class="rcap c-{cap_color or color}">{E(cap)}</span>' if cap else ""
    sub_html = f'<span class="rmeta">{sub}</span>' if sub else ""
    return (f'<a class="row" href="{href}" {extra_attr}>{tile(emo, color)}'
            f'<span class="rtx">{cap_html}<span class="rtt">{E(title)}</span>{sub_html}</span>{SVGS["chev"]}</a>')

# ---------- Kategorien ----------
_sp = [num(x["prot"]) for x in meals["snack"]]
CATS = [
 dict(id="fruehstueck", name="Frühstück", seg="Frühstück", color="orange", items=meals["frueh"], avg=SA[0],
      intro=f'Warmes Porridge und Overnight Oats für die Wochentage, Spiegelei und Rührei fürs Wochenende, die Skyr-Bowl für Morgen ohne Vorbereitung. Alle liegen bei {de(min(fk))} bis {de(max(fk))} kcal, du kannst also jederzeit tauschen.',
      filters=[]),
 dict(id="mittagessen", name="Mittagessen", seg="Mittag", color="green", items=meals["mittag"], avg=SA[1],
      intro="Nudeln, Reis, Burger und Burrito: Jedes Gericht hat Käse oder kräftige Röstaromen, damit es ohne Salz schmeckt. Die Tomaten-Feta-Pasta ist der Joker, wenn du ein Mittagessen tauschen willst. Kartoffeln gibt es nur als Pommes aus dem Airfryer, gewogen mit Schale.",
      filters=[("pasta", "Nudeln"), ("rice", "Reis"), ("hand", "Burger & Wrap")]),
 dict(id="snacks", name="Snacks", seg="Snacks", color="teal", items=meals["snack"], avg=SA[2],
      intro=f'Zwei süße und zwei herzhafte Snacks mit {de(min(_sp))} bis {de(max(_sp))} g Protein. Alle sind in 3 bis 5 Minuten fertig.',
      filters=[("snack", "Süß"), ("light", "Herzhaft")]),
 dict(id="suesses", name="Süßes", seg="Süßes", color="pink", items=sweets, avg=None, intro=sweet_sub,
      filters=[("pan", "Pfanne"), ("air", "Airfryer"), ("cold", "Kalt")]),
]

for c in CATS:
    for r in c["items"]:
        r["cat"] = c
        r["klabel"] = SWEET_KIND[r["kind"]] if c["id"] == "suesses" else r["kindlabel"]

plan_days = defaultdict(list)
for w in week:
    for m_ in w["meals"]:
        plan_days[m_[1]].append(w["d"])

def kcal_of(r):
    return f'{r["kcal"]} {r.get("unit", "kcal")}'

def recipe_row(r):
    c = r["cat"]
    q = " ".join([r["title"], r.get("short", ""), r["klabel"], c["name"]] + [x[0] for x in r["rows"] if len(x) > 1])
    meta = " · ".join([E(short_time(r["time"])), f'<span class="num">{E(kcal_of(r))}</span>', f'<span class="num">{E(r["prot"])}</span> Protein'])
    return row_link(f'#r/{r["id"]}', r["emo"], c["color"], r["title"], meta, r["klabel"],
                    extra_attr=f'data-kind="{r["kind"]}" data-q="{E(q.lower())}"').replace('class="row"', 'class="row rrow"', 1)

# ---------- Rezept-Detailseiten ----------
def ing_blocks(rows):
    out_, cur, head = "", [], ""
    def flush(h, items):
        if not items:
            return ""
        hh = f'<h3 class="ing-h">{E(h)}</h3>' if h else ""
        body = "".join(f'<div class="ing-r"><span class="nm">{E(a)}</span><span class="am num">{E(b)}</span></div>' for a, b in items)
        return f'{hh}<div class="ing">{body}</div>'
    for x in rows:
        if len(x) == 1:
            out_ += flush(head, cur)
            head, cur = x[0], []
        else:
            cur.append((x[0], x[1]))
    return out_ + flush(head, cur)

def steps_html(body, rid):
    b = BeautifulSoup(body, "html.parser")
    for ol in b.find_all("ol", class_="steps"):
        lis = ol.find_all("li", recursive=False)
        ol["data-rid"] = rid
        for i, li in enumerate(lis):
            inner_ = "".join(str(c) for c in li.contents).strip()
            li.clear()
            li["data-step"] = f"{rid}:{i}"
            frag = BeautifulSoup(
                f'<button type="button" class="stepck" aria-pressed="false" aria-label="Schritt {i + 1} abhaken">'
                f'<span class="n">{i + 1}</span>{SVGS["check"]}</button><div class="st">{inner_}</div>', "html.parser")
            for c in list(frag.contents):
                li.append(c)
        bar = BeautifulSoup(
            f'<div class="stepbar"><span class="sc-t"><b class="sc num">0 von {len(lis)}</b> erledigt</span>'
            f'<span class="sp"><i></i></span><button type="button" class="sreset">Zurücksetzen</button></div>', "html.parser")
        ol.insert_before(bar)
        hint = BeautifulSoup('<p class="shint">Tippe auf die Nummer, um einen Schritt abzuhaken. Die Häkchen verschwinden nach 2 Stunden von selbst.</p>', "html.parser")
        ol.insert_after(hint)
    for a in b.find_all("a", attrs={"data-open": True}):
        a["href"] = "#" + a["data-open"]
        del a["data-open"]
    return str(b)

def time_stat(t):
    m_ = re.match(r"^(ca\. )?(\d+)\s*(Min|Std)\b(.*)$", t)
    if not m_:
        return E(t), ""
    rest = m_.group(4).strip(" ,")
    rest = rest.replace("plus ", "+ ")
    pre = "ca. " if m_.group(1) else ""
    return f'{pre}{m_.group(2)}<span> {m_.group(3)}</span>', E(rest)

def stat(label, value_html, note=""):
    n = f'<em>{note}</em>' if note else ""
    return f'<div class="stat"><small>{label}</small><b class="num">{value_html}</b>{n}</div>'

def recipe_page(r):
    c, rid = r["cat"], r["id"]
    is_sweet = c["id"] == "suesses"
    kc_label = "Kalorien" + (f' {r["per"]}' if is_sweet and r.get("per") else "")
    prot_v = r["prot"].replace(" g", "")
    tv, tn = time_stat(r["time"])
    stats = [stat(kc_label, f'{r["kcal"]}<span> kcal</span>'), stat("Protein", f'{prot_v}<span> g</span>'), stat("Zeit", tv, tn)]
    days = plan_days.get(rid, [])
    plan = (f'<p class="r-plan">{SVGS["cal"]}<span>Im Wochenvorschlag: {", ".join(days)}</span></p>' if days else "")
    lead = r.get("leadtxt", "") if not is_sweet else f'{r["yld"]} · {r["price"]}' + (f' {r["per"]}' if r.get("per") else "")
    lead_html = f'<p class="r-lead">{E(lead)}</p>' if lead else ""
    fit = (f'<div class="fit"><b>So passt es in den Plan</b>{E(r["fit"])}</div>' if is_sweet else "")
    wz = ""
    if not is_sweet:
        v = msoup.find("div", attrs={"data-id": rid})
        w_ = v.find("div", class_="wuerz") if v else None
        if w_:
            wz = f'<h2 class="sh">Drei Sorten</h2><div class="wzgrid">{inner(w_)}</div>'
    nav_title = r.get("short") or r["title"]
    return f'''
<section class="page" id="pg-r-{rid}" data-route="r/{rid}" data-kind="recipe" data-title="{E(nav_title)}" hidden>
  {anc("r/" + rid)}
  {nav(nav_title, back="rezepte", right=WAKE_BTN)}
  <div class="pin wide">
    <div class="r-head">
      <div class="cover t-{c["color"]}" aria-hidden="true"><span>{r["emo"]}</span></div>
      <div class="r-htx lt">
        <p class="eyebrow c-{c["color"]}">{E(c["name"])} · {E(r["klabel"])}</p>
        <h1 class="ltitle r-title">{E(r["title"])}</h1>
        {lead_html}
        {plan}
      </div>
    </div>
    <div class="stats">{"".join(stats)}</div>
    {fit}
    {wz}
    <div class="rcols">
      <div class="r-ing"><h2 class="sh">Zutaten</h2>{ing_blocks(r["rows"])}</div>
      <div class="r-how"><h2 class="sh">Zubereitung</h2>{steps_html(r["body"], rid)}</div>
    </div>
  </div>
</section>'''

recipe_pages = "".join(recipe_page(r) for c in CATS for r in c["items"])
n_recipes = sum(len(c["items"]) for c in CATS)

# ---------- Rezepte-Übersicht ----------
def chips(c):
    if not c["filters"]:
        return ""
    btns = f'<button type="button" class="chip on" data-f="all">Alle <span>{len(c["items"])}</span></button>'
    for k, label in c["filters"]:
        n = sum(r["kind"] == k for r in c["items"])
        btns += f'<button type="button" class="chip" data-f="{k}">{E(label)} <span>{n}</span></button>'
    return f'<div class="chips" role="group" aria-label="Filter">{btns}</div>'

cat_html = ""
for c in CATS:
    stat_line = f'{len(c["items"])} Rezepte'
    if c["avg"]:
        stat_line += f' · Ø {c["avg"][0].strip("~")} kcal · {c["avg"][1].strip("~")} Protein'
    else:
        stat_line += " · wenig Zucker · ohne Salz"
    extra_top = (f'<div class="callout-s"><b>So passt es in den Plan</b>{E(sweet_rule)}</div>' if c["id"] == "suesses" else "")
    extra_bot = ""
    if c["id"] == "suesses":
        note = sweet_shopnote + ' Die Zusatz-Zutaten stehen in der <a href="#einkauf">Einkaufsliste</a> unter „Für Süßes“.'
        extra_bot = f'<p class="foot">{note}</p>'
    cat_html += f'''
    <div class="cat" data-cat="{c["id"]}" hidden>
      <div class="cat-h"><h2 class="cat-t">{E(c["name"])}</h2><span class="cat-n">{stat_line}</span></div>
      {extra_top}
      {chips(c)}
      <div class="list rlist">{"".join(recipe_row(r) for r in c["items"])}</div>
      <p class="foot cat-f">{E(c["intro"])}</p>
      {extra_bot}
    </div>'''

seg_html = "".join(f'<button type="button" role="tab" data-cat="{c["id"]}" aria-selected="false">{E(c["seg"])}</button>' for c in CATS)

# ---------- Woche ----------
SLOTS = [("Frühstück", "orange"), ("Mittag", "green"), ("Snack", "teal")]
WEEK2 = []
for w in week:
    ms = []
    for m_ in w["meals"]:
        r = byid[m_[1]]
        ms.append([r["short"], r["id"], r["emo"], r["kcal"], r["prot"], short_time(r["time"])])
    WEEK2.append(dict(d=w["d"], n=DAYN[DAYS.index(w["d"])], k=w["k"], p=w["p"], meals=ms))

days_html = "".join(f'<button type="button" class="day" role="tab" data-day="{i}" aria-selected="false"><span>{d}</span></button>' for i, d in enumerate(DAYS))
week_rows = ""
for i, w in enumerate(WEEK2):
    emos = "".join(f'<i class="t-{SLOTS[j][1]}">{m_[2]}</i>' for j, m_ in enumerate(w["meals"]))
    week_rows += (f'<button type="button" class="row wrow" data-day="{i}"><span class="wd">{w["n"]}</span><span class="wemo" aria-hidden="true">{emos}</span>'
                  f'<span class="wv"><b class="num">{w["k"]}</b><small class="num">{w["p"]}</small></span>{SVGS["chev"]}</button>')

def knum(s):
    return float(s.replace(".", "").replace(",", ".")) if s else 0.0

def sum_card(w, label):
    """Gleiches Markup wie sumCard() in app.js."""
    bar = "".join(f'<i class="b-{SLOTS[i][1]}" style="flex:{knum(m_[3]):g}"></i>' for i, m_ in enumerate(w["meals"]))
    aria = ", ".join(f'{SLOTS[i][0]} {m_[3]} kcal' for i, m_ in enumerate(w["meals"]))
    legend = "".join(f'<span><i class="dot b-{SLOTS[i][1]}"></i>{SLOTS[i][0]} <b class="num">{m_[3]}</b></span>' for i, m_ in enumerate(w["meals"]))
    return (f'<div class="sum-top"><div><div class="sum-l">{E(label)}</div><div class="sum-k num">{w["k"]}<small> kcal</small></div></div>'
            f'<div class="sum-side"><div><b class="num">{w["p"].replace(" g", "")}<span class="u"> g</span></b><small>Protein</small></div></div></div>'
            f'<div class="bar" role="img" aria-label="{E("Kalorien: " + aria)}">{bar}</div><div class="legend">{legend}</div>')

def meal_rows(w):
    """Gleiches Markup wie mealRows() in app.js."""
    return "".join(
        f'<a class="row" href="#r/{m_[1]}"><span class="tile t-{SLOTS[i][1]}" aria-hidden="true">{m_[2]}</span>'
        f'<span class="rtx"><span class="rcap c-{SLOTS[i][1]}">{SLOTS[i][0]}</span><span class="rtt">{E(m_[0])}</span>'
        f'<span class="rmeta">{E(m_[5])} · <span class="num">{m_[3]} kcal</span> · <span class="num">{m_[4]}</span> Protein</span></span>{SVGS["chev"]}</a>'
        for i, m_ in enumerate(w["meals"]))

day_blocks = "".join(f'<div class="dayblock" id="tag-{i}"><div class="card sum">{sum_card(w, w["n"])}</div><div class="list">{meal_rows(w)}</div></div>'
                     for i, w in enumerate(WEEK2))
week_links = ""
for i, w in enumerate(WEEK2):
    emos = "".join(f'<i class="t-{SLOTS[j][1]}">{m_[2]}</i>' for j, m_ in enumerate(w["meals"]))
    week_links += (f'<a class="row wrow" href="#tag-{i}"><span class="wd">{w["n"]}</span><span class="wemo" aria-hidden="true">{emos}</span>'
                   f'<span class="wv"><b class="num">{w["k"]}</b><small class="num">{w["p"]}</small></span>{SVGS["chev"]}</a>')

# ---------- Einkauf ----------
shop_groups_html, idx = "", 0
for g in groups:
    rows_ = ""
    for it in g["items"]:
        rows_ += (f'<label class="ck"><input type="checkbox" data-key="shop" data-i="{slug(it[0])}">'
                  f'<span class="cbox" aria-hidden="true">{SVGS["check"]}</span>'
                  f'<span class="ctext"><span class="cname">{E(it[0])}</span><small>{E(it[1])}</small></span>'
                  f'<span class="cprice num">{E(it[-1])}</span></label>')
        idx += 1
    opt = " opt" if g.get("optional") else ""
    shop_groups_html += (f'<div class="sg{opt}"><div class="sgh"><h2>{E(g["name"])}</h2><span class="num">{de(g["total"], 2)} €</span></div>'
                         f'<p class="sgn">{E(g["note"])}</p><div class="list">{rows_}</div></div>')
RING_C = 2 * 3.14159265 * 24

# ---------- Wissen ----------
def mobile_tables(html_):
    b = BeautifulSoup(html_, "html.parser")
    for t in b.find_all("table"):
        heads = [th.get_text(" ", strip=True) for th in t.find_all("th")]
        for tr in t.find_all("tr"):
            for j, td in enumerate(tr.find_all("td")):
                kids = [k for k in td.contents if getattr(k, "name", None) or str(k).strip()]
                if len(kids) == 1 and getattr(kids[0], "name", None) == "span" and "pill" in (kids[0].get("class") or []):
                    td["class"] = (td.get("class") or []) + ["pc"]
                    tr["class"] = (tr.get("class") or []) + ["haspill"]
                elif j > 0 and j < len(heads) and heads[j]:
                    td["data-label"] = heads[j]
    for a in b.find_all("a", attrs={"data-open": True}):
        a["href"] = "#" + a["data-open"]
        del a["data-open"]
    return str(b)

ARTICLES = [
 ("✨", "orange", "Lecker ohne Salz", "Warum es tot geschmeckt hat, die 7 Regeln für jedes Rezept und ein Abschmeck-Check", LECKER, "prose"),
 ("⚡", "yellow", "Schneller kochen", "Sieben Tricks, damit es nach der Uni schnell geht", SCHNELL, "prose"),
 ("💬", "blue", "Ehrlich gesagt", ehrlich[0], ehrlich[1], "callout" if ehrlich[2] else "prose"),
 ("⏱️", "teal", "So läuft der Tag", tag_sub, tag_html, "prose"),
 ("🍳", "green", "Küchen-Grundlagen", kueche[0], kueche[1], "prose"),
 ("🌀", "indigo", "Airfryer-Technik", airfryer[0], airfryer[1], "prose"),
 ("🧬", "pink", "Bekommst du genug Vitamine?", vitamine[0], vitamine[1], "prose"),
]
wissen_rows, article_pages = "", ""
for icon, color, title, sub_, content, cls in ARTICLES:
    sl = slug(title)
    wissen_rows += row_link(f"#w/{sl}", icon, color, title, E(sub_)).replace('class="rmeta"', 'class="rmeta clamp2"')
    article_pages += f'''
<section class="page" id="pg-w-{sl}" data-route="w/{sl}" data-kind="article" data-title="{E(title)}" hidden>
  {anc("w/" + sl)}
  {nav(title, back="wissen")}
  <div class="pin">
    <div class="lt a-head">{tile(icon, color, "big")}<h1 class="ltitle">{E(title)}</h1><p class="desc">{E(sub_)}</p></div>
    <div class="article {cls}">{mobile_tables(content)}</div>
  </div>
</section>'''

tabbar = "".join(f'<a class="tab" href="#{k}" data-tab="{k}">{TAB_ICONS[k]}<span>{n}</span></a>' for k, n in TABS)
sidebar_items = "".join(f'<a class="side-i" href="#{k}" data-tab="{k}">{TAB_ICONS[k]}<span>{n}</span></a>' for k, n in TABS)

page = f'''<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Ernährungsplan</title>
<meta name="description" content="{VERSION} – Frühstück, Mittag und Snack, schnell und lecker ohne Salz, rund {de(avg_k)} kcal und {de(avg_p)} g Protein am Tag">
<meta name="theme-color" content="#f2f2f7">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Ernährung">
<meta name="mobile-web-app-capable" content="yes">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ctext y='.9em' font-size='88'%3E%F0%9F%A5%97%3C/text%3E%3C/svg%3E">
<link rel="apple-touch-icon" href="data:image/png;base64,{ICON_B64}">
<script>
document.documentElement.classList.add("js");
(function(){{var t=null;try{{t=localStorage.getItem("ep-theme");}}catch(e){{}}
if(!t)t=window.matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light";
document.documentElement.setAttribute("data-theme",t);
var m=document.querySelector('meta[name="theme-color"]');if(m)m.content=t==="dark"?"#000000":"#f2f2f7";}})();
</script>
<style>
{CSS}
</style>
</head>
<body>
<aside class="side" aria-label="Navigation">
  <div class="side-h"><span class="side-ic" aria-hidden="true">🥗</span><div><b>Ernährungsplan</b><small>{VERSION}</small></div></div>
  <nav class="side-n">{sidebar_items}</nav>
  <button class="side-theme" type="button" data-theme-toggle>{SVGS["moon"]}{SVGS["sun"]}<span class="t-l">Dunkles Design</span><span class="t-d">Helles Design</span></button>
</aside>

<main class="main" id="main">

<section class="page" id="pg-heute" data-route="heute" data-title="Heute">
  {anc("heute")}
  {nav("Heute", right=THEME_BTN)}
  <div class="pin">
    <div class="lt"><p class="eyebrow" id="todayDate">Heute</p><h1 class="ltitle">Heute</h1></div>
    <div class="card sum jsonly" id="todaySum"></div>
    <h2 class="gh jsonly">Mahlzeiten</h2>
    <div class="list jsonly" id="todayList"></div>
    <h2 class="gh nojs">Deine Woche</h2>
    <div class="list nojs">{week_links}</div>
    <p class="foot">Laut Wochenvorschlag, ohne Abendessen. Im Schnitt sind es {de(avg_k)} kcal und {de(avg_p)} g Protein am Tag, die Woche kostet rund {COST_DAY_S} € pro Tag.</p>
    <h2 class="gh">Gut zu wissen</h2>
    <div class="list">
      {row_link("#w/lecker-ohne-salz", "✨", "orange", "Lecker ohne Salz", "Warum es tot geschmeckt hat und was jetzt in jedem Rezept anders ist")}
      {row_link("#w/schneller-kochen", "⚡", "yellow", "Schneller kochen", "Sieben Tricks, damit es nach der Uni schnell geht")}
    </div>
  </div>
</section>

<section class="page" id="pg-rezepte" data-route="rezepte" data-title="Rezepte" hidden>
  {anc("rezepte")}
  {nav("Rezepte", right=THEME_BTN)}
  <div class="pin">
    <div class="lt"><p class="eyebrow">{n_recipes} Rezepte · ohne Salz</p><h1 class="ltitle">Rezepte</h1></div>
    <div class="search">{SVGS["search"]}<input type="search" id="q" placeholder="Rezepte und Zutaten suchen" autocomplete="off" enterkeyhint="search" aria-label="Rezepte und Zutaten suchen"><button type="button" class="sx" id="qx" aria-label="Suche löschen" hidden>×</button></div>
    <div class="seg" id="seg" role="tablist" aria-label="Kategorie" style="--n:{len(CATS)}">{seg_html}<span class="seg-thumb" aria-hidden="true"></span></div>
    {cat_html}
    <p class="empty" id="noRes" hidden>Kein Rezept gefunden. Versuch es mit einer Zutat wie „Käse“ oder „Reis“.</p>
  </div>
</section>

<section class="page" id="pg-woche" data-route="woche" data-title="Woche" hidden>
  {anc("woche")}
  {nav("Woche", right=THEME_BTN)}
  <div class="pin">
    <div class="lt"><p class="eyebrow">Wochenvorschlag</p><h1 class="ltitle">Woche</h1></div>
    <p class="desc">Frühstück, Mittag und Snack für jeden Tag, ohne Abendessen. Die Einkaufsliste ist genau darauf abgestimmt.</p>
    <div class="days jsonly" id="days" role="tablist" aria-label="Wochentag">{days_html}</div>
    <div class="card sum jsonly" id="daySum"></div>
    <div class="list jsonly" id="dayList"></div>
    <h2 class="gh jsonly">Alle Tage</h2>
    <div class="list jsonly" id="weekList">{week_rows}</div>
    <div class="nojs">{day_blocks}</div>
    <p class="foot">{week_note}</p>
  </div>
</section>

<section class="page" id="pg-einkauf" data-route="einkauf" data-title="Einkauf" hidden>
  {anc("einkauf")}
  {nav("Einkauf", right=THEME_BTN)}
  <div class="pin">
    <div class="lt"><p class="eyebrow">Kaufland · Richtpreise</p><h1 class="ltitle">Einkauf</h1></div>
    <div class="card pcard">
      <svg class="ring" viewBox="0 0 60 60" aria-hidden="true"><circle class="rg-bg" cx="30" cy="30" r="24"/><circle class="rg-fg" id="shopRing" cx="30" cy="30" r="24" stroke-dasharray="{RING_C:.2f}" stroke-dashoffset="{RING_C:.2f}"/></svg>
      <div class="pc-t"><b class="num" id="shopCount">0 von {n_shop}</b><small id="shopSub">erledigt</small></div>
      <div class="pc-b"><button type="button" class="btn" id="hideDone" aria-pressed="false">Erledigte ausblenden</button><button type="button" class="btn red" data-reset="shop">Zurücksetzen</button></div>
    </div>
    <div class="stats three">
      {stat("1. Einkauf", f"{de(first_buy)}<span> €</span>", "mit Vorrat und Gewürzen")}
      {stat("Jede Woche", f"{de(weekly)}<span> €</span>", "nur das Frische")}
      {stat("Pro Tag", f"{COST_DAY_S}<span> €</span>", "echte Kosten")}
    </div>
    <p class="desc">Alles für den Wochenvorschlag, inklusive Gewürze, Senf und Essig. Kaufland-Eigenmarke, Preise sind Richtwerte.</p>
    <div id="shopLists">{shop_groups_html}</div>
    <h2 class="gh">Gut zu wissen</h2>
    <div class="card notes">{shop_note}</div>
  </div>
</section>

<section class="page" id="pg-wissen" data-route="wissen" data-title="Wissen" hidden>
  {anc("wissen")}
  {nav("Wissen", right=THEME_BTN)}
  <div class="pin">
    <div class="lt"><p class="eyebrow">Hintergrund</p><h1 class="ltitle">Wissen</h1></div>
    <div class="list">{wissen_rows}</div>
    <p class="foot">{E(footer)}</p>
  </div>
</section>
{recipe_pages}
{article_pages}
</main>

<div class="edge-b" aria-hidden="true"></div>
<nav class="tabbar" aria-label="Hauptnavigation">{tabbar}</nav>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
<script>
const WEEK = {json.dumps(WEEK2, ensure_ascii=False)};
{JS}
</script>
<script>if(!window.EP_OK)document.documentElement.classList.remove("js");</script>
</body>
</html>'''

open(out, "w", encoding="utf-8").write(page)
print("ok", len(page), {c["id"]: len(c["items"]) for c in CATS}, "shop", n_shop,
      "first", round(first_buy, 2), "weekly", round(weekly, 2), "avg", round(avg_k), round(avg_p, 1))
for w in WEEK2:
    print(w["d"], w["k"], w["p"])
