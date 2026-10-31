"""Exact store positions from OpenStreetMap, for the chains whose own lists give only the town.
Output rows: [chain, name, lat, lng]. The app uses them instead of town-centre guesses."""
import re, json, time
import requests

OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
QUERY = """[out:json][timeout:120];
area["ISO3166-1"="MK"][admin_level=2]->.mk;
(nwr["shop"~"^(supermarket|convenience|grocery|wholesale|department_store)$"](area.mk););
out center tags;"""

CHAINS = [  # (chain id as in prices.json, pattern on name/brand/operator, pattern that rules a match out)
    ("Kipper", r"kipper|ки[п]+ер", None),
    ("KAM", r"^\s*(kam|кам)\b|\bkam market|\bкам маркет", r"камен|kamen|камп|kamp"),
    ("Stokomak", r"stokomak|стокомак", None),
    ("Zito", r"\b(žito|zito|жито)\b", r"\bleb\b|\bлеб\b|pekar|пекар|bakery"),
    ("Spar", r"\bspar\b|\bспар\b", None),
    ("Zur", r"\b(žur|zur|жур)\b", None),
    ("Vero", r"\b(vero|веро)\b", r"eurofarm|farm|аптек|apteka|baklava"),
    ("Ramstore", r"ramstore|рамстор", r"mall|мол\b"),
    ("Misa", r"\b(miša|misa|миша)\b|mkb", None),
    ("Angromarketing", r"angro ?marketing|ангро ?маркетинг", None),
    ("Tamaro", r"tamaro|тамаро", None),
    ("Elida", r"\b(elida|елида)\b", None),
    ("Crvena Ruza", r"crvena ru[zž]a|црвена ружа", None),
    ("DIM", r"^\s*(dim|дим)\b", None),
    ("ATVA", r"\b(atva|атва)\b", None),
]
CX = [(c, re.compile(p, re.I), re.compile(x, re.I) if x else None) for c, p, x in CHAINS]

def fetch_osm():
    last = None
    for url in OVERPASS:
        for i in range(2):
            try:
                r = requests.post(url, data={"data": QUERY}, timeout=180, headers={"User-Agent": "PazarPriceBot/1.0"})
                r.raise_for_status(); return r.json().get("elements", [])
            except Exception as e:
                last = e; time.sleep(10)
    raise RuntimeError(f"overpass: {last}")

def chain_stores(elements):
    out, seen = [], set()
    for e in elements:
        t = e.get("tags", {})
        lat = e.get("lat") or (e.get("center") or {}).get("lat"); lng = e.get("lon") or (e.get("center") or {}).get("lon")
        if lat is None or lng is None: continue
        text = " | ".join(t.get(k, "") for k in ("brand", "name", "name:mk", "name:en", "name:sq", "operator"))
        for c, rx, ex in CX:
            if rx.search(text) and not (ex and ex.search(text)):
                key = (c, round(lat, 4), round(lng, 4))
                if key in seen: break
                seen.add(key)
                addr = " ".join(x for x in (t.get("addr:street", ""), t.get("addr:housenumber", "")) if x).strip()
                out.append([c, (t.get("name") or c)[:60] + (f", {addr}" if addr else ""), round(lat, 5), round(lng, 5)])
                break
    return out

if __name__ == "__main__":
    s = chain_stores(fetch_osm())
    import collections
    print(len(s), collections.Counter(x[0] for x in s))
