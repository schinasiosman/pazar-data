"""Official company logos, collected once and refreshed weekly by the daily job.
1. the logo in the company's Wikipedia article (infobox), else
2. the logo on the company's own website (apple-touch-icon / <img … logo …> / og:logo), then
3. cleaned up the same way for every company: on white, trimmed, centred in a square, 256 px PNG.
Output: site/logos/<id>.png and the list of ids that have one."""
import io, os, re, json, time, html, urllib.parse
import requests
from PIL import Image, ImageChops

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 PazarLogoBot/1.0"}
# Wikipedia and Wikimedia only answer bots that say who they are (a browser name from a server is refused)
WM_UA = {"User-Agent": "PazarLogoBot/1.1 (https://github.com/schinasiosman/pazar-data) python-requests"}
def wm_get(url, **kw):
    for i in range(4):
        r = requests.get(url, headers=WM_UA, timeout=30, **kw)
        if r.status_code != 429 and r.status_code < 500: return r
        time.sleep(3 * (i + 1))
    return r

# Wikipedia article (any language) whose infobox shows the logo
WIKI = {
 "imlek":"sr:Имлек","president":"en:Président (brand)","galbani":"en:Galbani","zott":"en:Zott","megle":"en:Meggle","perutnina":"en:Perutnina Ptuj","gavrilovic":"en:Gavrilović",
 "neoplanta":"sr:Неопланта","pik":"en:PIK Vrbovec","podravka":"en:Podravka","vegeta":"en:Vegeta (condiment)","kotanyi":"de:Kotányi","barilla":"en:Barilla Group","divela":"en:Divella",
 "uncleBens":"en:Ben's Original","riso":"it:Riso Scotti","zvijezda":"hr:Zvijezda (tvrtka)","monini":"it:Monini","riomare":"en:Rio Mare","calvo":"es:Grupo Calvo","delamaris":"sl:Delamaris",
 "hellmanns":"en:Hellmann's and Best Foods","heinz":"en:Heinz","kikkoman":"en:Kikkoman","drOetker":"en:Dr. Oetker","nestle":"en:Nestlé","kelloggs":"en:Kellogg's","nutella":"en:Nutella",
 "nescafe":"en:Nescafé","lavazza":"en:Lavazza","frank":"hr:Franck (tvrtka)","teekanne":"en:Teekanne","lipton":"en:Lipton",
 "alkaloid":"en:Alkaloid AD Skopje","ledo":"en:Ledo (company)","frikom":"sr:Фриком","mccain":"en:McCain Foods","magnum":"en:Magnum (ice cream)","algida":"en:Heartbrand","milka":"en:Milka",
 "kras":"en:Kraš","bambi":"sr:Бамби (предузеће)","jaffa":"sr:Јафа Црвенка","oreo":"en:Oreo","stark":"sr:Штарк","pringles":"en:Pringles","lays":"en:Lay's",
 "doritos":"en:Doritos","sevendays":"en:Chipita","haribo":"en:Haribo","orbit":"en:Orbit (gum)","lindt":"en:Lindt & Sprüngli","kinder":"en:Kinder (brand)","pionir":"sr:Пионир (предузеће)",
 "swisslion":"en:Swisslion","snickers":"en:Snickers","marbo":"sr:Марбо","rosen":"en:Roshen","cocacola":"en:Coca-Cola","pepsi":"en:Pepsi","fanta":"en:Fanta","sprite":"en:Sprite (drink)",
 "schweppes":"en:Schweppes","sinalko":"en:Sinalco","mirinda":"en:Mirinda","cappy":"en:Cappy","pfanner":"de:Pfanner","cedevita":"en:Cedevita","knjaz":"sr:Књаз Милош (предузеће)",
 "redbull":"en:Red Bull","monster":"en:Monster Energy","fuzetea":"en:Fuze Tea","heineken":"en:Heineken","amstel":"en:Amstel Brewery","lasko":"en:Laško Brewery",
 "niksicko":"en:Nikšićko pivo","tuborg":"en:Tuborg","stella":"en:Stella Artois","efes":"en:Efes Beverage Group","tikves":"en:Tikveš (winery)","jackdaniels":"en:Jack Daniel's",
 "johnnie":"en:Johnnie Walker","jameson":"en:Jameson Irish Whiskey","smirnoff":"en:Smirnoff","absolut":"en:Absolut Vodka","gordons":"en:Gordon's Gin","jager":"en:Jägermeister",
 "baileys":"en:Baileys Irish Cream","badel":"en:Badel 1862","ariel":"en:Ariel (detergent)","persil":"en:Persil","lenor":"en:Lenor","silan":"de:Silan (Marke)","fairy":"en:Fairy (brand)",
 "finish":"en:Finish (detergent)","somat":"de:Somat","domestos":"en:Domestos","cif":"en:Cif (cleaning product)","mrproper":"en:Mr. Clean","zewa":"en:Essity","paloma":"sl:Paloma (podjetje)",
 "vileda":"en:Vileda","headshoulders":"en:Head & Shoulders","pantene":"en:Pantene","nivea":"en:Nivea","dove":"en:Dove (toiletries)","palmolive":"en:Palmolive (brand)","garnier":"en:Garnier",
 "colgate":"en:Colgate (toothpaste)","aquafresh":"en:Aquafresh","oralb":"en:Oral-B","elmex":"de:Elmex","rexona":"en:Rexona","borotalco":"it:Borotalco","gillette":"en:Gillette",
 "always":"en:Always (brand)","pampers":"en:Pampers","huggies":"en:Huggies","hipp":"file:HIPP-Logo.svg","whiskas":"en:Whiskas","pedigree":"en:Pedigree Petfoods",
 "friskies":"en:Friskies","sutas":"tr:Sütaş","bonduelle":"en:Bonduelle","libresse":"en:Libresse","oldspice":"en:Old Spice","kitkat":"en:Kit Kat","tictac":"en:Tic Tac","indomie":"en:Indomie",
 "muller":"en:Müller (company)","schauma":"de:Schauma","kitekat":"en:Kitekat","eti":"tr:Eti (şirket)","seara":"pt:Seara Alimentos","helios":"sr:Хелиос (предузеће)","argeta":"en:Argeta",
 "koka":"hr:Koka (tvrtka)","pivka":"sl:Pivka perutninarstvo","zlatiborac":"sr:Златиборац","carnex":"sr:Карнекс","dijamant":"sr:Дијамант (предузеће)","nikolaus":"de:Nikolaus (Wodka)",
 "koro":"hr:Koro (tvrtka)","viva":"sr:Вива (сок)","next":"sr:Некст (сок)","bravo":"sr:Браво (сок)","rosa":"sr:Роса (вода)","kozuf":"mk:Кожуф (вода)",
 "kim":"mk:КИМ (компанија)","vitaminka":"mk:Витаминка","pelisterka":"mk:Пелистерка","bimilk":"mk:Бимилк","zito":"mk:Жито Лукс","zitoluks":"mk:Жито Лукс","stobi":"mk:Стоби (компанија)",
 "evropa":"mk:Европа (компанија)","pekabesko":"mk:Пекабеско","bitolsko":"mk:Млекара Битола","vemilk":"mk:Вемилк","korab":"mk:Кораб Трница","bovin":"en:Bovin (winery)","popov":"en:Popova Kula",
 "stobiWine":"en:Stobi Winery","imako":"mk:Имако вино","dalvina":"en:Dalvina winery","zlatendab":"mk:Златен Даб","gorska":"mk:Горска (вода)",
}
# companies' own websites (used when there is no Wikipedia logo)
SITE = {
 "bimilk":"bimilk.com.mk","radovo":"mlekarnicaradovo.mk","vemilk":"vemilk.com.mk","bitolsko":"mlekarabitola.com.mk","korab":"korab-trnica.com.mk","bucen":"bucenkozjak.com.mk","zdenka":"zdenka.hr",
 "olimpus":"olympus.gr","salakis":"salakis.gr","pekabesko":"pekabesko.com","mein":"mein.com.mk","soleta":"soleta.com.mk","podgorka":"podgorka.mk","celopek":"celopek.com.mk","grozdanovski":"grozdanovski.com.mk",
 "zito":"zito.com.mk","zitoluks":"zitoluks.com.mk","zitopolog":"zitopolog.com.mk","dondon":"dondon.rs","algomak":"algomak.mk","bonito":"bonito.com.mk","vitaminka":"vitaminka.com.mk",
 "alpojo":"alpojo.com.mk","kibela":"kibela.com.mk","sonceva":"soncevadolina.mk","maks":"maks.com.mk","polimark":"polimark.com.mk","vipro":"vipro.com.mk","evia":"evia.com.mk","grindeli":"grindeli.com",
 "kim":"kim.com.mk","vitalia":"vitalia.rs","dauti":"dauti.com.mk","bako":"bako.mk","nutini":"nutini.mk","bon":"bonvivant.mk","riskosa":"riscossa.it","perfetto":"perfetto.mk","dijamant":"dijamant.rs",
 "brilijant":"brilijant.mk","biser":"biser.com.mk","balko":"balko.mk","tomi":"tomi.com.mk","luma":"luma.mk","grand":"grandkafa.com","pela":"pela.mk",
 "minas":"minas.mk","koro":"koro.hr","jumis":"jumis.mk","perfetto":"perfetto.mk","stobi":"stobi.com.mk","evropa":"evropa.com.mk","vincini":"vincini.rs","fruktal":"fruktal.si","jippi":"jippi.rs",
 "rosa":"rosavoda.rs","pelisterka":"pelisterka.com.mk","kozuf":"kozuf.com","jana":"jana.hr","gorska":"gorska.com.mk","dobra":"dobravoda.mk","izvorska":"izvorska.mk","heba":"heba.rs","mivela":"mivela.com",
 "guarana":"guarana.rs","hell":"hellenergy.com","zlatendab":"skopskopivo.com.mk","lazar":"vinarijalazar.mk","imako":"imakovino.com","violeta":"violeta.com","perfex":"perfex.com.mk",
 "paclan":"paclan.pl","fino":"fino.com.mk","teo":"teo.bg","afrodita":"afrodita.com.mk","bebivita":"bebivita.de","bekutan":"becutan.rs","idealsipka":"idealsipka.com.mk","grekos":"grekos.com.mk",
 "vitanez":"vitanez.com.mk","salti":"salti.mk","drbenner":"drbenner.com","ornel":"ornel.com.tr","kristal":"kristal.mk","martino":"martino.com.mk","amalfi":"amalficosmetics.com",
 "adrijus":"adrijus.mk","fritoso":"fritoso.com","krugsen":"krugsen.com.mk","nakoma":"nakoma.com.mk","helena":"helena.mk","hisar":"hisar.com.mk","gora":"gora.com.mk","dolcia":"dolcia.mk",
 "halta":"halta.si","viki":"viki.mk","herba":"herba.mk","semana":"semana.com.mk","busto":"busto.mk","kroko":"kroko.mk","twisty":"twisty.mk","hans":"hans.mk","bebeto":"bebeto.com","perex":"perex.mk",
 "kisko":"kisko.mk","kralimarko":"pivarnicakralimarko.mk","tika":"tika.mk","martex":"martex.mk","gradus":"gradus.mk","orion":"orion.mk","valdor":"valdor.mk","dobarden":"dobarden.mk","polo":"polo.mk",
 "lecker":"lecker.com.mk","tiamo":"tiamo.mk","zogi":"zogi.mk","mena":"mena.mk","fini":"fini.mk","vudi":"vudi.mk","kampona":"kambona.mk","dime":"dime.mk","hepi":"hepi.mk","tremnik":"tremnik.mk",
 "samoilova":"samoilova.mk","aleksandrija":"aleksandrija.mk","kame":"kame.mk","bifruit":"bifruit.mk","dentinal":"dentinal.mk","karlina":"karlina.mk","novito":"novito.mk","okidoki":"okidoki.mk",
 "gurmano":"gurmano.mk","uno":"uno.mk","cattos":"cattos.com","zvijezda":"zvijezda.hr","floriol":"floriol.mk","ferara":"ferrara.mk","ella":"ella.mk","koka":"koka.hr","cekin":"cekin.com.mk",
 "neoplanta":"neoplanta.rs","klas":"klas.mk","melissa":"melissa.gr","basso":"basso.it","iliada":"iliada.gr","imlek":"imlek.rs","kozjak":"kozjak.mk","sevendays":"7days.com","jacobs":"jacobs.de","aptamil":"aptaclub.co.uk","skopsko":"skopskopivo.com.mk",
}

LOGO_KEY = re.compile(r'\|\s*(?:logo|лого|logo_image|image_logo|logotip|logosu|logó)\s*=\s*(?:\[\[(?:File|Датотека|Податотека|Слика|Datei|Image|Datoteka|Dosya):)?([^\n|\]]+\.(?:svg|png|jpg|jpeg|gif))', re.I)
NOT_LOGO = re.compile(r'commons-logo|wikidata|wiktionary|wikiquote|foodlogo|bier|flag|map|karte|question_book|edit-clear|ambox|symbol_support|disambig', re.I)

def _thumb(lang, files, wiki="wikipedia"):
    """file names -> 400 px image URLs (SVGs come back as PNG thumbnails)"""
    host = "commons.wikimedia.org" if wiki == "commons" else f"{lang}.wikipedia.org"
    r = wm_get(f"https://{host}/w/api.php", params={"action": "query", "format": "json", "prop": "imageinfo", "iiprop": "url", "iiurlwidth": 500,
                     "titles": "|".join("File:" + f.strip().replace("_", " ") for f in files[:10])})
    out = []
    for p in r.json().get("query", {}).get("pages", {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        u = ii.get("thumburl") or ii.get("url")
        if u: out.append(u)
    return out

def wiki_logo(spec):
    """The official logo of the company in a Wikipedia article, as a list of image URLs to try, best first:
    1. the logo named in the article's infobox, 2. the company's logo on Wikidata (P154), 3. a picture in the article whose file name says 'logo'.
    The article's lead photo is never used: it is usually a product or a building, not the logo."""
    lang, title = spec.split(":", 1)
    if lang == "file": return _thumb("", [title], "commons")             # a logo file on Wikimedia Commons
    api = f"https://{lang}.wikipedia.org/w/api.php"; urls = []
    r = wm_get(api, params={"action": "parse", "format": "json", "redirects": 1, "page": title, "prop": "wikitext", "section": 0}).json()
    wt = (r.get("parse", {}).get("wikitext") or {}).get("*", "")
    m = LOGO_KEY.search(wt)
    if m and not NOT_LOGO.search(m.group(1)): urls += _thumb(lang, [m.group(1)])
    q = wm_get(api, params={"action": "query", "format": "json", "redirects": 1, "titles": title, "prop": "pageprops|images", "ppprop": "wikibase_item", "imlimit": 50}).json()
    for p in q.get("query", {}).get("pages", {}).values():
        qid = (p.get("pageprops") or {}).get("wikibase_item")
        if qid:
            e = wm_get("https://www.wikidata.org/w/api.php", params={"action": "wbgetclaims", "format": "json", "entity": qid, "property": "P154"}).json()
            files = [c["mainsnak"]["datavalue"]["value"] for c in e.get("claims", {}).get("P154", []) if c.get("mainsnak", {}).get("datavalue")]
            if files: urls += _thumb(lang, files[-1:], "commons")              # the newest logo
        names = [i["title"].split(":", 1)[1] for i in p.get("images", [])]
        key = re.sub(r"\W+", "", title.split("(")[0]).lower()[:5]
        logos = [n for n in names if re.search(r"logo|лого", n, re.I) and not NOT_LOGO.search(n) and (not key or key in re.sub(r"\W+", "", n).lower() or len(names) < 6)]
        if logos: urls += _thumb(lang, logos[:2])
    seen = set(); return [u for u in urls if not (u in seen or seen.add(u))]

def site_logo(domain, bid=""):
    """Only a logo that names the company (in its file name, alt text or class) is taken: shops' sites also show partners' logos."""
    stem = re.sub(r"[^a-z]", "", domain.split(".")[0].lower())
    keys = {k for k in (stem[:5], re.sub(r"[^a-z]", "", bid.lower())[:5]) if len(k) >= 3}
    own = any(k in stem for k in keys if k != stem[:5]) or not bid
    for scheme in ("https://", "http://"):
        try:
            r = requests.get(scheme + domain, headers=UA, timeout=25); r.raise_for_status(); base = r.url; t = r.text; break
        except Exception: t = None
    if not t: return None
    cands = []
    for m in re.finditer(r'<img[^>]+>', t, re.I):
        tag = m.group(0)
        if re.search(r'logo', tag, re.I) and any(k in re.sub(r'[^a-z]', '', tag.lower()) for k in keys):
            src = re.search(r'(?:src|data-src)=["\']([^"\']+)', tag)
            if src: cands.append((0, src.group(1)))
    for m in re.finditer(r'<link[^>]+rel=["\'][^"\']*apple-touch-icon[^"\']*["\'][^>]*>', t, re.I):
        h = re.search(r'href=["\']([^"\']+)', m.group(0))
        if h and own: cands.append((1, h.group(1)))           # the site's own icon only when the site is the brand's
    m = re.search(r'<meta[^>]+property=["\']og:logo["\'][^>]+content=["\']([^"\']+)', t, re.I)
    if m and own: cands.append((0, m.group(1)))
    return [urllib.parse.urljoin(base, html.unescape(u)) for _, u in sorted(cands, key=lambda x: x[0])][:4] or None

def to_png(url, size=256):
    r = wm_get(url) if "wikimedia.org" in url or "wikipedia.org" in url else requests.get(url, headers=UA, timeout=30)
    r.raise_for_status(); data = r.content
    if url.lower().split("?")[0].endswith(".svg") or data[:200].lstrip().startswith((b"<svg", b"<?xml")):
        import cairosvg
        data = cairosvg.svg2png(bytestring=data, output_width=600)
    im = Image.open(io.BytesIO(data)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255)); bg.alpha_composite(im); im = bg.convert("RGB")
    diff = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255)))
    box = diff.point(lambda x: 255 if x > 18 else 0).getbbox()
    if not box: return None
    im = im.crop(box); w, h = im.size
    if max(w, h) < 40: return None                              # a tiny favicon is not a logo
    ink = sum(1 for px in im.convert("L").resize((64, 64)).getdata() if px < 235) / 4096
    if ink < 0.02: return None                                     # almost empty (white logo on white)
    side = int(max(w, h) * 1.16); can = Image.new("RGB", (side, side), (255, 255, 255))
    can.paste(im, ((side - w) // 2, (side - h) // 2)); can = can.resize((size, size), Image.LANCZOS)
    return can

def collect(brand_ids, out_dir, keep_days=7):
    os.makedirs(out_dir, exist_ok=True); have, report = [], {}
    for b in brand_ids:
        path = os.path.join(out_dir, f"{b}.png")
        if os.path.exists(path) and time.time() - os.path.getmtime(path) < keep_days * 86400:
            have.append(b); continue
        urls = []
        try:
            if b in WIKI:
                urls += wiki_logo(WIKI[b])
        except Exception as e: report[b] = f"wiki: {e}"[:120]
        try:
            if b in SITE: urls += site_logo(SITE[b], b) or []
        except Exception as e: report[b] = f"site: {e}"[:120]
        for u in urls:
            try:
                im = to_png(u)
                if im: im.save(path, optimize=True); have.append(b); report[b] = "ok " + u[:100]; break
            except Exception as e: report[b] = f"img: {e}"[:120]
        else:
            if os.path.exists(path): have.append(b)                  # keep last week's logo
            report.setdefault(b, "none")
        time.sleep(0.3)
    return sorted(set(have)), report
