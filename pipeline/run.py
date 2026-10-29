"""Daily job: download price lists -> recognise products -> group the same product across chains -> data/prices.json"""
import json, os, re, sys, time, collections, hashlib, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fetch import fetch_all, photos
from classify import classify, PRODUCE
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
    return ' '.join(out)

def build(raw):
    groups = collections.defaultdict(lambda: {'rows': [], 'w': 0})
    for c, rows in raw.items():
        for r in rows:
            if not r or not r[0] or not r[1]: continue
            g, n = classify(r[0])
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
            b = brand_of(n); fat = ''
            if g in FAT:
                m = re.search(r'(\d+(?:[.,]\d+)?) ?%', n); fat = m.group(1).replace(',', '.') if m else ''
            key = (g, b, tuple(s), fat) if b else ((g, '', tuple(s), fat) if g in FRESHISH else (g, '#' + re.sub(r'[\d.,/x%]+[a-z]*', '', n).strip()[:40], tuple(s), fat))
            groups[key]['rows'].append((c, r)); groups[key]['w'] = groups[key]['w'] or w
    prods = collections.defaultdict(list)
    for (g, b, s, fat), v in groups.items():
        pr = {}
        for c, r in v['rows']:
            p = float(r[1]); reg = float(r[3]) if len(r) > 3 and r[3] and float(r[3]) > p else 0
            if c not in pr or p < pr[c][0]: pr[c] = (p, reg)
        names = [r[0] for c, r in v['rows'] if c in CYR_SRC] or [r[0] for c, r in v['rows']]
        prods[(g, b)].append({'s': s, 't': nice(collections.Counter(names).most_common(1)[0][0]), 'p': pr, 'w': v['w']})
    tot = collections.Counter(g for (g, b), v in prods.items() for x in v)
    rows, used = [], set()
    for (g, b), v in prods.items():
        for x in v:
            if not (len(x['p']) >= 2 or not b.startswith('#') or tot[g] < 25): continue
            bid = 'fresh' if b == '' else ('other' if b.startswith('#') else b); used.add(bid)
            val, u, mult = x['s']; pr = [0] * len(CH); reg = {}
            for c, (p, r) in x['p'].items():
                i = CH.index(c); pr[i] = round(p)
                if r and r > p: reg[str(i)] = round(r)
            rows.append([g, bid, x['t'], val, u, mult, pr, reg] + ([1] if x['w'] else []))
    col = lambda s: '#%06x' % (int(hashlib.md5(s.encode()).hexdigest()[:6], 16) & 0x7f7f7f)
    brs = {b: [BN[b][0], col(b), BN[b][1]] for b in used if b in BN}
    return brs, rows

def match_photos(rows, ph):
    """Pictures for products: the same product (type, company, size) in Ramstore's online shop;
    every product type and company also gets one picture to show when its own is missing."""
    imgs, ix = [], {}
    def add(path):
        if path not in ix: ix[path] = len(imgs); imgs.append(path)
        return ix[path]
    exact, bytype, bybrand = {}, collections.defaultdict(list), collections.defaultdict(list)
    for name, path, price in ph:
        g, n = classify(name)
        if not g: continue
        s = size(n); b = brand_of(n)
        if s: exact.setdefault((g, b, round(s[0] * s[2]), s[1]), path)
        bytype[g].append((0 if not b else 1, len(n), path, b))
        if b: bybrand[b].append((len(n), path))
    ri = []
    for r in rows:
        g, bid, t, val, u, mult = r[:6]
        b = '' if bid in ('fresh', 'other') else bid
        p = exact.get((g, b, round(val * mult), u)) if b else None
        
        ri.append(add(p) if p else -1)
    pop = collections.Counter((r[0], r[1]) for r in rows)              # how many products each company has in that type
    def rep(g, v): return sorted(v, key=lambda x: (-pop[(g, x[3])], x[1]))[0][2]
    gimg = {g: add(rep(g, v)) for g, v in bytype.items()}
    wp = os.path.join(DATA, "wiki_photos.json")          # free photos (Wikimedia Commons) for fruit & veg and types the shop lacks
    if os.path.exists(wp):
        for g, url in json.load(open(wp)).items():
            if g in PRODUCE or g not in gimg: gimg[g] = add(url)
    bimg = {b: add(sorted(v)[0][1]) for b, v in bybrand.items()}
    return {"base": "https://ramstoredodoma.com.mk/images/thumbs/", "list": imgs, "rows": ri, "types": gimg, "brands": bimg}

if __name__ == "__main__":
    prev_raw = None
    p = os.path.join(DATA, "raw.json")
    if os.path.exists(p): prev_raw = json.load(open(p))
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
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=1))).strftime("%d.%m.%Y")
    out = {"v": 1, "date": today, "built": int(time.time()), "chains": CH, "brands": brs, "rows": rows, "img": img, "report": report}
    if len(rows) < 1000: print("Too few products, not publishing", len(rows), report); sys.exit(1)
    json.dump(out, open(os.path.join(DATA, "prices.json"), "w"), ensure_ascii=False, separators=(",", ":"))
    print(json.dumps(report, ensure_ascii=False, indent=1)); print("products", len(rows), "brands", len(brs))
