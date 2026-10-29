"""Put data/prices.json into the app file as its built-in prices: python pipeline/embed.py path/to/pazar.html"""
import json, re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "data", "prices.json")))
p = sys.argv[1]; h = open(p, encoding="utf-8").read()
J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
h = re.sub(r'^let PRICE_DATE=".*?";$', lambda m: f'let PRICE_DATE="{d["date"]}";', h, count=1, flags=re.M)
h = re.sub(r'^let REAL_BR=.*;$', lambda m: "let REAL_BR=" + J(d["brands"]) + ";", h, count=1, flags=re.M)
h = re.sub(r'^let REAL=.*;$', lambda m: "let REAL=" + J(d["rows"]) + ";", h, count=1, flags=re.M)
if "img" in d: h = re.sub(r'^let IMG=.*;$', lambda m: "let IMG=" + J(d["img"]) + ";", h, count=1, flags=re.M)
h = re.sub(r"\(collected [\d.]+\)", f"(collected {d['date']})", h, count=1)
open(p, "w", encoding="utf-8").write(h); print("embedded", len(d["rows"]), "products from", d["date"])
