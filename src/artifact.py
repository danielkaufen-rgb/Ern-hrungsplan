"""Macht aus index.html die Fassung fürs Artifact auf claude.ai, das Doctype, html, head und body selbst liefert.
Aufruf: cd src && python3 artifact.py ../index.html <ziel.html>"""
import re, sys

src, out = sys.argv[1:3]
s = open(src, encoding="utf-8").read()
head = re.search(r"<head>(.*?)</head>", s, re.S).group(1)
body = re.search(r"<body>(.*)</body>", s, re.S).group(1)
head = re.sub(r'<meta charset="utf-8">\s*', "", head)
head = re.sub(r'<meta name="viewport"[^>]*>\s*', "", head)
head = re.sub(r"<title>[^<]*</title>\s*", "", head)
head = head.replace('document.documentElement.classList.add("js");',
                    'document.documentElement.classList.add("js");document.documentElement.lang="de";', 1)
frag = "<title>Mein Ernährungsplan</title>\n" + head.strip() + "\n" + body.strip() + "\n"
for tag in ("<!DOCTYPE", "<html", "<head>", "<body>", "</html>"):
    if tag in frag:
        raise SystemExit(f"{tag} steht noch im Fragment")
open(out, "w", encoding="utf-8").write(frag)
print("ok", len(frag))
