"""Download today's published price lists of the supermarket chains.
Each chain gives rows of [name, price, description, regular price]."""
import re, io, json, time, html, sys, concurrent.futures as cf
import requests

S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0 (Linux; Android 14) PazarPriceBot/1.0 (+https://github.com)"
TIMEOUT = 60

def num(s):
    """'71 ден.', '145.00', '157,00', '1.299,00', '1,299.00' -> float"""
    if s is None: return 0.0
    if isinstance(s, (int, float)): return float(s)
    m = re.search(r"\d[\d.,]*", str(s).replace(" ", "").replace("\u00a0", ""))
    if not m: return 0.0
    t = m.group().rstrip(".,")
    if "," in t and "." in t:
        dec = "," if t.rfind(",") > t.rfind(".") else "."
        t = t.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif "," in t:
        t = t.replace(",", ".") if re.search(r",\d{1,2}$", t) else t.replace(",", "")
    elif t.count(".") == 1 and re.search(r"\.\d{3}$", t) and len(t) > 5:
        t = t.replace(".", "")
    try: return float(t)
    except ValueError: return 0.0

def get(url, **kw):
    for i in range(4):
        try:
            r = S.get(url, timeout=TIMEOUT, **kw); r.raise_for_status(); return r
        except Exception as e:
            if i == 3: raise
            time.sleep(3 * (i + 1))

def post(url, data):
    for i in range(4):
        try:
            r = S.post(url, data=data, timeout=TIMEOUT); r.raise_for_status(); return r
        except Exception:
            if i == 3: raise
            time.sleep(3 * (i + 1))

def cells(tr_html):
    return [html.unescape(re.sub(r"<[^>]+>", " ", c)).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", tr_html, re.S)]

def rows_of(page):
    return [cells(tr) for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S)]

# ---- Kipper: WordPress DataTable endpoint, one store
def kipper():
    # Kipper's site refuses plain scripts; look like the browser page that loads the table
    h = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
         "Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest",
         "Origin": "https://kipper.mk", "Referer": "https://kipper.mk/", "Accept-Language": "mk,en;q=0.8"}
    try: S.get("https://kipper.mk/", headers=h, timeout=TIMEOUT)
    except Exception: pass
    r = S.post("https://kipper.mk/wp-admin/admin-ajax.php", data={"action": "get_products_data", "post_id": "22662", "draw": "1", "start": "0", "length": "10000"}, headers=h, timeout=TIMEOUT)
    r.raise_for_status(); j = r.json()
    return [[x["product_name"], num(x["product_price"]), x.get("product_subgroup") or "", num(x.get("product_price_normal")) or num(x["product_price"]), x.get("product_name_alt") or ""] for x in j["data"]]

def _kipper_old():
    j = post("https://kipper.mk/wp-admin/admin-ajax.php", {"action": "get_products_data", "post_id": "22662", "draw": "1", "start": "0", "length": "10000"}).json()
    return [[x["product_name"], num(x["product_price"]), x.get("product_subgroup") or "", num(x.get("product_price_normal")) or num(x["product_price"]), x.get("product_name_alt") or ""] for x in j["data"]]

# ---- proverkanaceni.mk: same system for several chains, 100 rows per page
def proverka(sub):
    base = f"https://{sub}.proverkanaceni.mk/"
    first = get(base).text
    orgs = re.findall(r'<option value="(\d+)"', first)
    org = orgs[0] if orgs else "1"
    out, page = [], 1
    while page < 400:
        t = get(f"{base}?page={page}&perPage=100&search=&org={org}").text
        rs = [r for r in rows_of(t) if len(r) >= 6 and num(r[1])]
        if not rs: break
        out += [[r[0], num(r[1]), r[3], num(r[5]) or num(r[1])] for r in rs]
        if f"page={page+1}&" not in t: break
        page += 1; time.sleep(0.2)
    return out

# ---- Spar: JSON API, several stores, names written with YUSCII letters
YU = str.maketrans({"@": "Ž", "[": "Š", "\\": "Đ", "]": "Ć", "^": "Č", "`": "ž", "{": "š", "|": "đ", "}": "ć", "~": "č"})
def spar():
    seen = {}
    for store in (3, 1, 2, 7):
        page = 1
        while True:
            j = get(f"https://api.prod.spar.mk/api/pricelists-web/{store}/products?per_page=500&page={page}").json()
            for x in j["data"]:
                if str(x.get("available")) != "1": continue
                name = (x.get("name") or "").translate(YU)
                if name in seen: continue
                sale = num(x.get("sale") or x.get("discount_price") or x.get("regular"))
                seen[name] = [name, sale, x.get("category") or "", num(x.get("regular")) or sale]
            if page >= j["meta"]["last_page"]: break
            page += 1; time.sleep(0.15)
    return list(seen.values())

# ---- Žur and DIM: WordPress endpoint returning table rows
def zur(action, org):
    j = post("https://ceni.zur.mk/wp-admin/admin-ajax.php", {"action": action, "org": org, "page": "1", "search": "", "limit": "10000"}).json()
    return [[r[1], num(r[2]), r[4], num(r[6]) or num(r[2])] for r in rows_of(j["data"]["html"]) if len(r) >= 7]

# ---- Vero: numbered static pages
def vero():
    out, n = [], 1
    while n < 300:
        r = S.get(f"https://pricelist.vero.com.mk/116_{n}.html", timeout=TIMEOUT)
        if r.status_code != 200: break
        r.encoding = "utf-8"
        rs = [x for x in rows_of(r.text) if len(x) >= 6 and num(x[1])]
        if not rs: break
        out += [[x[0], num(x[1]), x[4], num(x[5]) or num(x[1])] for x in rs]
        if f"116_{n+1}.html" not in r.text: break
        n += 1; time.sleep(0.2)
    return out

# ---- Ramstore: one big table on the store page
def ramstore():
    t = get("https://ramstore.com.mk/marketi/ramstore-siti-mol/").text
    return [[r[0], num(r[1]), r[3], num(r[5]) or num(r[1])] for r in rows_of(t) if len(r) >= 6 and num(r[1])]

# ---- KAM: each store publishes a PDF
def kam():
    import pdfplumber
    shops = post("https://kam.com.mk/ShopsWeb/LoadShopList", {}).json()
    shop = next((s for s in shops if s["Id"] == 95 and s.get("ShopFiles")), None) or next(s for s in shops if s.get("ShopFiles"))
    pdf = get("https://kam.com.mk/" + shop["ShopFiles"][0]["RelativePath"]).content
    out = []
    with pdfplumber.open(io.BytesIO(pdf)) as p:
        for pg in p.pages:
            for tb in pg.extract_tables():
                for r in tb:
                    if not r or not r[0] or not r[1] or not num(r[1]): continue
                    c = [re.sub(r"\s+", " ", x or "").strip() for x in r]
                    out.append([c[0], num(c[1]), c[3], num(c[5]) or num(c[1])])
    return out

# ---- ATVA: JSON API with every product
def atva():
    j = get("https://ceni.atva.mk/api/products").json()
    return [[x["Ime_Na_Artikl"], num(x["Cena"]), x.get("Ime_Na_Podgrupa") or "", num(x["Cena"])] for x in j if str(x.get("Aktiven")) == "1"]


# ---- Product photos: Ramstore's online shop (ramstoredodoma.com.mk) lists products with pictures, 15 per page
IMG_BASE = "https://ramstoredodoma.com.mk/images/thumbs/"
def photos():
    """returns [[name, image path after IMG_BASE, price]]"""
    def page(n):
        h = post("https://ramstoredodoma.com.mk/Catalog/OBAjaxFilterProducts",
                 {"cid": "0", "isc": "true", "mid": "0", "vid": "0", "sid": "true", "adv": "true", "PagingFilteringContext[PageNumber]": str(n)}).text
        out = []
        for it in re.findall(r'<div class="product-item".*?(?=<div class="product-item"|$)', h, re.S):
            t = re.search(r'class="product-title">\s*<a[^>]*>(.*?)</a>', it, re.S); im = re.search(r'(?:data-lazyloadsrc|src)="/images/thumbs/([^"]+)"', it)
            pr = re.search(r'actual-price">([^<]+)<', it)
            if t and im and "default-image" not in im.group(1): out.append([html.unescape(t.group(1)).strip(), im.group(1), num(pr.group(1)) if pr else 0])
        last = re.search(r'changePage\((\d+)\);">\s*Последно', h) or re.search(r'last-page"><a href="javascript:obajaxfilter.changePage\((\d+)\)', h)
        return out, int(last.group(1)) if last else n
    first, last = page(1); rows = first
    with cf.ThreadPoolExecutor(4) as ex:
        for r, _ in ex.map(page, range(2, min(last, 2000) + 1)): rows += r
    seen = set(); return [r for r in rows if not (r[0] in seen or seen.add(r[0]))]

SOURCES = {
    "Kipper": kipper,
    "Stokomak": lambda: proverka("stokomak"), "Zito": lambda: proverka("zito"), "Misa": lambda: proverka("mkbmisa"),
    "Angromarketing": lambda: proverka("angromarketing"), "Tamaro": lambda: proverka("tamaro"), "Elida": lambda: proverka("elida"),
    "Crvena Ruza": lambda: proverka("crvenaruza"),
    "Zur": lambda: zur("load_prices_data", "5"), "DIM": lambda: zur("load_dimceni_prices_data", "18"),
    "Spar": spar, "Vero": vero, "Ramstore": ramstore, "KAM": kam, "ATVA": atva,
}

def fetch_all(previous=None):
    """Returns {chain: rows}. A chain that fails keeps yesterday's rows, so one broken site doesn't empty the app."""
    out, report = {}, {}
    with cf.ThreadPoolExecutor(6) as ex:
        futs = {ex.submit(fn): name for name, fn in SOURCES.items()}
        for f in cf.as_completed(futs):
            name = futs[f]
            try:
                rows = f.result()
                if len(rows) < 50: raise RuntimeError(f"only {len(rows)} rows")
                out[name] = rows; report[name] = ["ok", len(rows)]
            except Exception as e:
                report[name] = ["failed", str(e)[:200]]
                if previous and previous.get(name): out[name] = previous[name]; report[name].append("kept previous")
    return out, report

if __name__ == "__main__":
    which = sys.argv[1:] or list(SOURCES)
    for w in which:
        t = time.time(); rows = SOURCES[w]()
        print(w, len(rows), round(time.time() - t, 1), "s", rows[:2])
