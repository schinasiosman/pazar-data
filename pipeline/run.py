"""Daily job: download price lists -> recognise products -> group the same product across chains -> data/prices.json"""
import json, os, re, sys, time, collections, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fetch import fetch_all, photos
from classify import classify, PRODUCE
from categories import TYPE_GROUPS, FRESH_TYPES, FRESH_BRANDS
from tags import tags_of, variety_of
from brands import B
from norm import size

ROOT = os.path.dirname(HERE); DATA = os.path.join(ROOT, "data"); os.makedirs(DATA, exist_ok=True)
CH = ["Kipper","KAM","Stokomak","Zito","Spar","Zur","Vero","Ramstore","Misa","Angromarketing","Tamaro","Elida","Crvena Ruza","DIM","ATVA"]
CYR_SRC = set(CH) - {"Spar"}
FRESHISH = PRODUCE | {'wholeChicken','chickenBreast','chickenThighs','chickenWings','mince','beefMince','porkNeck','porkChops','beefStew','steak','lamb','trout','salmon','seaBream'}
FAT = {'milk','yogurt','kefir','sourCream','cream','whiteCheese','kashkaval','butter','ayran'}
HERBS = {'parsley','dill','freshHerbs','springOnion'}
PERKG = re.compile(r'\b(kg|kgr|kilo|refus)\b|/kg|/kgr')
PCS_OK = ('eggs','toiletPaper','kitchenRoll','napkins','diapers','babyWipes','pads','dishTabs','binBags','sponges','razors','tea','rolls','pitaBread','tortillas','croissant','cakes','toothbrush','soap')
BR = [(i, re.compile(r)) for i, _, _, r in B]
BN = {i: (l, c) for i, l, c, _ in B}

def brand_of(n):
    for i, rx in BR:
        if rx.search(n): return i
    return ''

def nice(t):
    t = re.sub(r'[`~^{}\[\]|@?]+', '', str(t)); t = re.sub(r'\s+', ' ', t).strip(' .-/')
    out = []
    for x in t.split(' '):
        lx = x.lower()
        out.append(lx if re.match(r'^[\d.,/x*%]+[a-zа-ш.]*$', lx) else lx[:1].upper() + lx[1:])
    t = ' '.join(out)
    return re.sub(r'(\d\s?(?:g|gr|kg|kgr|ml|l|г|гр|кг|кгр|мл|л)\.?)\s+\d{1,2}$', r'\1', t, flags=re.I)   # 'Шекер 800г 10' -> 'Шекер 800г'

NO_CAT = {"KAM", "Zur", "DIM"}          # these lists have no shelf category (KAM repeats the name there)

def build(raw):
    # 1. recognise every row
    items = []
    for c, rows in raw.items():
        for r in rows:
            if not r or not r[0] or not r[1]: continue
            g, n = classify(r[0], "" if c in NO_CAT or len(r) < 3 else r[2])
            if not g: continue
            s = size(n); w = 0
            if g == 'eggs':                                   # eggs: '10/1', '30 kom' -> 60 g each, never by weight
                m = re.search(r'\b(\d{1,2})\s*(?:/\s*1\b|/|kom\b|br\b|pcs\b|x\b)', n)
                if not m or not (4 <= int(m.group(1)) <= 60): continue
                s = (int(m.group(1)) * 60.0, 'g', 1)
            elif g in HERBS and (not s or s[1] == 'pcs' or re.search(r'kitk|vrsk|\bpar\b', n)):
                s = (50.0 * (s[0] if s and s[1] == 'pcs' and s[0] < 10 else 1), 'g', 1)   # a bunch of herbs is about 50 g
            if not s:
                if PERKG.search(n) or g in FRESHISH: s = (1000.0, 'g', 1); w = 1
                else: continue
            if s[1] == 'pcs' and g not in PCS_OK:
                if g in FRESHISH: s = (1000.0, 'g', 1); w = 1
                else: continue
            b = brand_of(n)
            if g in FRESH_TYPES and b not in FRESH_BRANDS: b = ''           # tomatoes, onions, fresh meat: no fake brands
            fat = ''
            if g in FAT:
                m = re.search(r'(\d+(?:[.,]\d+)?) ?%', n); fat = m.group(1).replace(',', '.') if m else ''
            items.append([c, r, g, n, tuple(s), w, b, fat])
    # 2. a company name only counts where that company really sells: 'Max' on a croissant doesn't make garlic 'Max'
    bg = collections.defaultdict(collections.Counter)
    for it in items:
        if it[6]:
            for grp in TYPE_GROUPS.get(it[2], {"?"}): bg[it[6]][grp] += 1
    for it in items:
        b = it[6]
        if not b: continue
        cnt = bg[b]; top = cnt.most_common(1)[0][0]; mine = TYPE_GROUPS.get(it[2], {"?"})
        if top not in mine and max(cnt[x] for x in mine) < 3: it[6] = ''
    # 3. group the same product across chains
    groups = collections.defaultdict(lambda: {'rows': [], 'w': 0})
    for c, r, g, n, s, w, b, fat in items:
        key = (g, b, s, fat) if b else ((g, '~' + '+'.join(variety_of(n)), s, fat) if g in FRESHISH else (g, '#' + re.sub(r'[\d.,/x%]+[a-z]*', '', n).strip()[:40], s, fat))
        groups[key]['rows'].append((c, r, n)); groups[key]['w'] = groups[key]['w'] or w
    prods = collections.defaultdict(list)
    for (g, b, s, fat), v in groups.items():
        pr = {}
        allp = sorted(float(r[1]) for c, r, n in v['rows'])
        med = allp[len(allp) // 2]
        for c, r, n in v['rows']:
            p = float(r[1]); reg = float(r[3]) if len(r) > 3 and r[3] and float(r[3]) > p else 0
            if len(allp) >= 4 and not (0.5 * med <= p <= 2.2 * med): continue      # a different product or unit hiding under the same name
            if c not in pr or p < pr[c][0]: pr[c] = (p, reg)
        if not pr: continue
        names = [r[0] for c, r, n in v['rows'] if c in CYR_SRC] or [r[0] for c, r, n in v['rows']]
        nn = collections.Counter(n for c, r, n in v['rows']).most_common(1)[0][0]
        prods[(g, b)].append({'s': s, 't': nice(collections.Counter(names).most_common(1)[0][0]), 'p': pr, 'w': v['w'], 'tags': (b[1:].split('+') if b.startswith('~') and len(b) > 1 else []) + tags_of(nn, g, fat)})
    tot = collections.Counter(g for (g, b), v in prods.items() for x in v)
    rows, used = [], set()
    for (g, b), v in prods.items():
        for x in v:
            if not (len(x['p']) >= 2 or not b.startswith('#') or tot[g] < 25): continue
            bid = 'fresh' if (b == '' or b.startswith('~')) else ('other' if b.startswith('#') else b); used.add(bid)
            val, u, mult = x['s']; pr = [0] * len(CH); reg = {}
            for c, (p, r) in x['p'].items():
                i = CH.index(c); pr[i] = round(p)
                if r and r > p: reg[str(i)] = round(r)
            rows.append([g, bid, x['t'], val, u, mult, pr, reg, x['w'], x['tags']])
    col = lambda s: '#%06x' % (int(hashlib.md5(s.encode()).hexdigest()[:6], 16) & 0x7f7f7f)
    brs = {b: [BN[b][0], col(b), BN[b][1]] for b in used if b in BN}
    return brs, rows

def match_photos(rows, ph):
    """Pictures: a product's own photo (same type, company and size in Ramstore's online shop), otherwise a photo of
    the same company's product of that type, otherwise a neutral photo of that kind of food. Never another brand's product."""
    imgs, ix = [], {}
    def add(path):
        if path not in ix: ix[path] = len(imgs); imgs.append(path)
        return ix[path]
    exact, bytb, plain = {}, collections.defaultdict(list), collections.defaultdict(list)
    for name, path, price in ph:
        g, n = classify(name)
        if not g: continue
        s = size(n); b = brand_of(n)
        if g in FRESH_TYPES and b not in FRESH_BRANDS: b = ''
        if s and b: exact.setdefault((g, b, round(s[0] * s[2]), s[1]), path)
        if b: bytb[(g, b)].append((len(n), path))
        else: plain[g].append((len(n), path))
    ri = []
    for r in rows:
        g, bid, t, val, u, mult = r[:6]
        p = exact.get((g, bid, round(val * mult), u)) if bid not in ('fresh', 'other') else None
        ri.append(add(p) if p else -1)
    gimg = {}
    wp = os.path.join(DATA, "wiki_photos.json")          # free photos (Wikimedia Commons) of each kind of food
    if os.path.exists(wp):
        for g, url in json.load(open(wp)).items(): gimg[g] = add(url)
    for g, v in plain.items():
        if g not in gimg: gimg[g] = add(sorted(v)[0][1])
    tb = {f"{g}|{b}": add(sorted(v)[0][1]) for (g, b), v in bytb.items()}
    return {"base": "https://ramstoredodoma.com.mk/images/thumbs/", "list": imgs, "rows": ri, "types": gimg, "tb": tb, "brands": {}}

if __name__ == "__main__":
    prev_raw = None
    p = os.path.join(DATA, "raw.json")
    if os.path.exists(p): prev_raw = json.load(open(p))
    sp = os.path.join(DATA, "seed_raw.json.gz")     # saved lists from a manual collection: used for a chain that has never downloaded
    if os.path.exists(sp):
        import gzip
        seed = json.load(gzip.open(sp, "rt", encoding="utf-8")); prev_raw = prev_raw or {}
        for k, v in seed.items():
            if not prev_raw.get(k): prev_raw[k] = v
    if len(sys.argv) > 1 and sys.argv[1] == "--offline":      # rebuild from the saved raw lists only
        raw, report = prev_raw, {"offline": True}
    else:
        raw, report = fetch_all(prev_raw)
    json.dump(raw, open(p, "w"), ensure_ascii=False)
    brs, rows = build(raw)
    pp = os.path.join(DATA, "photos.json"); ph = json.load(open(pp)) if os.path.exists(pp) else []
    if "--offline" not in sys.argv:
        try:
            new = photos()
            if len(new) > 500: ph = new; json.dump(ph, open(pp, "w"), ensure_ascii=False); report["photos"] = ["ok", len(ph)]
        except Exception as e: report["photos"] = ["failed", str(e)[:200], "kept previous"]
    img = match_photos(rows, ph)
    # same-looking product photos (white square) and official company logos, published with the website
    logos = []
    if "--offline" not in sys.argv:
        site = os.path.join(ROOT, "site")
        try:
            from logos import collect, to_png
            logos, lrep = collect(sorted(brs), os.path.join(site, "logos")); report["logos"] = ["ok", len(logos)]
            json.dump(lrep, open(os.path.join(DATA, "logos_report.json"), "w"), ensure_ascii=False, indent=0)
        except Exception as e: report["logos"] = ["failed", str(e)[:200]]
        try:
            os.makedirs(os.path.join(site, "img"), exist_ok=True); done = 0
            for i, path in enumerate(img["list"]):
                if path.startswith("http"): continue
                try:
                    im = to_png(img["base"] + path, 320)
                    if im: im.save(os.path.join(site, "img", f"{i}.jpg"), quality=84); img["list"][i] = f"img/{i}.jpg"; done += 1
                except Exception: pass
            img["local"] = True; report["photos_clean"] = ["ok", done]
        except Exception as e: report["photos_clean"] = ["failed", str(e)[:200]]
    sp2 = os.path.join(DATA, "stores.json"); stores = json.load(open(sp2)) if os.path.exists(sp2) else []
    if "--offline" not in sys.argv:
        try:
            from stores import fetch_osm, chain_stores
            new = chain_stores(fetch_osm())
            if len(new) > 50: stores = new; json.dump(stores, open(sp2, "w"), ensure_ascii=False); report["stores"] = ["ok", len(stores)]
        except Exception as e: report["stores"] = ["failed", str(e)[:200], "kept previous"]
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).strftime("%d.%m.%Y")
    dp = os.path.join(DATA, "raw_date.txt")
    if "--offline" in sys.argv and os.path.exists(dp): today = open(dp).read().strip()      # rebuilt from saved lists: keep their date
    elif "--offline" not in sys.argv: open(dp, "w").write(today)
    out = {"v": 2, "date": today, "built": int(time.time()), "chains": CH, "brands": brs, "rows": rows, "img": img, "logos": logos, "stores": stores, "report": report}
    if len(rows) < 1000: print("Too few products, not publishing", len(rows), report); sys.exit(1)
    json.dump(out, open(os.path.join(DATA, "prices.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print(json.dumps(report, ensure_ascii=False, indent=1)); print("products", len(rows), "brands", len(brs))
