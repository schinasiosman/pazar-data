import json,re,sys
sys.path.insert(0,__import__('os').path.dirname(__file__))
from norm import norm,size
from rules import R,X_NONFOOD
NONFOOD_FIRST={'laundry','softener','dishSoap','dishTabs','cleaner','bleach','toiletPaper','kitchenRoll','napkins','binBags','sponges','foil','shampoo','conditioner','showerGel','soap','toothpaste','toothbrush','deodorant','razors','pads','handCream','diapers','babyWipes','babyFood','catFood','dogFood','babyFormula'}
R2=[r for r in R if r[0] in NONFOOD_FIRST]+[r for r in R if r[0] not in NONFOOD_FIRST]
RC=[(g,re.compile(i),re.compile(x) if x else None) for g,i,x in R2]
NONFOOD_OK={'laundry','softener','dishSoap','dishTabs','cleaner','bleach','toiletPaper','kitchenRoll','napkins','binBags','sponges','foil','shampoo','conditioner','showerGel','soap','toothpaste','toothbrush','deodorant','razors','pads','handCream','diapers','babyWipes','babyFood','catFood','dogFood','babyFormula'}
XN=re.compile(X_NONFOOD)
FOODX=re.compile(r'za telo|za lice|za kosa|hidrat|nivea|bekutan|afrodita|garnier|palmoliv|\bfeja\b|hajlajter|hulahop|cetka|solja|forma za|sad za|t\.voda|tecen det|\bstr 8\b|cupkalk|pire\b|nutrino|kasick|argeta|pasteta|\bset za\b|kupka|sapun|sampon|krema za|krem za (lice|race|telo|raka)|losion|gel za|\btus\b|deterd|sredstv|omeknuv|vlazn|peleni|hrana za|za mac|za kuc|kozmet|sprej|osvez|parfem|toalet|igrack|ukras|dekor|kalap|modla|presa za|sokovnik|cedalka|cinij|drzac|toster|aparat|\btava\b|lonec|energizer|bater|svek|\bmaska\b|labelo|balsam|kondicioner|regenerat|stapcinja za usi|vreki|kesi\b|folij|caši|casi\b|kutij|hartij|lepak|boja za|boi za|velikdensk|novogodis|sijalic|tablet za|vitamin c tablet|suplement|kapsul')
PRODUCE={'apples','bananas','oranges','mandarins','lemons','limes','grapes','pears','peaches','strawberries','watermelon','kiwi','plums','mango','avocado','tomatoes','cucumbers','peppers','hotPeppers','potatoes','sweetPotato','onions','springOnion','garlic','ginger','carrots','cabbage','lettuce','zucchini','eggplant','spinach','broccoli','cauliflower','mushrooms','celery','leek','beetroot','pumpkin','parsley','dill','freshHerbs'}
PROCESSED=re.compile(r'\b\w*\d{4,}\w*\b|cevitan|resana|praline|drink|tablet|finis|\bviva\b|bandit|cevce|septona|hipp|hippis|\blino\b|salata|noze|ekofrost|noiset|krugsen|vitalia|kranci|coko|mini |sok|nektar|dzem|marmel|kasa|kasick|cips|bonbon|caj|jogurt|sladoled|pire|sus|konz|tegla|ocet|turs|zacin|sos|supa|corba|pita|burek|krem|smuti|pijal|napit|vkus|aroma|kolac|keks|biskv|vafl|cokolad|gumen|zele|liker|rakij|vino|frikom|ledo|zamrz|smrz|pecen|pohovan|salata so|polnet|krekeri|grick|stapc|flips|pukank|mleko|puding|desert|bar\b|kompot|sirup|cedevit|osvez|tabla|seme|semk')
PANTRY_CAP={'cocoa','flour','sugar','salt','rice','oil','eggs','butter','coffee','honey','yeast'}
EXTRA_X={k:re.compile(v) for k,v in {
 'milk':r'jojoba|telo|losion|cokol|kakao|coko',
 'beefStew':r'pita|lazanj|tortel|ravio',
 'cocoa':r'alva|zelje|najlepse|hulahop|krem|kolac|tort|sladoled|kroas|med i orev|napolit|cokol|rolls|valc|target|dejs',
 'eggs':r'coko|dzigo|kinder|cokolad|forma|sokolad|zelje|testenin|majonez',
 'sugar':r'neskafe|halta|banana|3 vo 1|so seker|bez se[kc]er|krem|krofn|\bset\b|zasladuv|sladil|stevia|bonbon',
 'yogurt':r'kolac|cupkalk|biskv|bar\b|kaf',
 'butter':r'\bleb\b|baget|sad za|jatki|seminja|so puter|biskv|keks|kolac|kroasan',
 'chickenBreast':r'argeta|pastet|junior|pohovan|panir|nagets|stapc|supa',
 'wholeChicken':r'pauc|pedigr|junior|oriz|medeljon|kaska|pohovan|nagets|stapc|krilc|gradi|file|bat|ukras|velikden|kocka|supa|hrana',
 'honey':r'srce|pionir|medenj|med\.|susam|sesam|\bbar\b|pastil|stapc|bonbon|krem|caj|lizal|so med|med i|sirup|\b\d{2} ?gr?\b',
 'coffee':r'solja|aparat|filter|kapsul|cokolad|bonbon|liker',
 'water':r'tonik|parfem|kozmet|det|gel|meriks',
 'oil':r'za sadovi|kozmet|bebi|masaz',
 'whiteCheese':r'magi|maggi|ideja|sos|zacin|kraks|grick|cips',
 'potatoes':r'fritoso|klinovi|pomfrit|kroket|aviko',
 'onions':r'aviko|krugovi|fritoso|pohovan',
}.items()}
DRINKS={'energy','icedTea','beer','redWine','whiteWine','roseWine','rakija','whisky','vodka','gin','liqueur','tonic','cola','orangeSoda','lemonSoda','mineral','sparklingWater','water','orangeJuice','appleJuice','fruitJuice','milk','ayran','kefir'}
from categories import fits, NOT_FRESH_PRODUCE, NOT_FRESH_MEAT, GROUP_TYPES
_PRODUCE_T=set(GROUP_TYPES["produce"].split()); _MEAT_T=set(GROUP_TYPES["meat"].split())
def classify(name, cat=None):
    """Product type of a price-list row. A type is only given when the name fits it AND the chain's shelf category fits it;
    otherwise the next rule is tried (so 'chicken slices' falls through to cold cuts, 'chicken' cat food to pet food)."""
    n=norm(name); c=norm(str(cat or ""))
    for g,inc,exc in RC:
        if inc.search(n) and not (exc and exc.search(n)):
            if not fits(g, c): continue
            if g in _PRODUCE_T and NOT_FRESH_PRODUCE.search(n): continue
            if g in _MEAT_T and NOT_FRESH_MEAT.search(n): continue
            if g not in NONFOOD_FIRST:
                if XN.search(n) or FOODX.search(n): return None,n
                if g in PRODUCE:
                    if PROCESSED.search(n) or len(n.split())>5: continue
                    s=size(n)
                    if s and (s[1]=='ml' or (s[1]=='g' and s[0]<150)): continue
                if g in PANTRY_CAP and len(n.split())>8: continue
                if g in EXTRA_X and EXTRA_X[g].search(n): continue
                if g in DRINKS:
                    s=size(n)
                    if not s or s[1]!='ml': continue
            return g,n
    return None,n
