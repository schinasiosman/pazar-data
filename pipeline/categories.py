"""The chains' own shelf categories, used to check that a product really is the kind of thing its name suggests.
A chocolate 'Kinder' egg in the sweets shelf can't become eggs; 'Chicken' cat food in the pet shelf can't become chicken."""
import re

# Shelf groups. Each product type belongs to one group (TYPE_GROUP below).
# Category keywords are on normalised (Latin, lowercase) category text; first matching rules win, several can match.
CAT_RULES = [
    # things that are never groceries we compare
    ("nonfood", r'cigar|tekstil|obuvk|igrack|igarck|igracki|alati|zelezar|skolsk|kanc|knig|books|lighter|plate for|ukras|rodenden|zabava|karneval|dekorac|sveki|ramki|novini|spisani|baterii|obleka|hulahop|carap|avtomobil|kujnski pribor|oprema za kujna|aksesoar za gotv|sadovi za domak|plastic|plasticn|staklo$|lesno krslivi|dnevna soba|\bbanja\b|crtanje|racna izrab|ambalaza|universal grip|nail|pencil|kika hair|boja za kosa|farb|color with|parfem|parfim|toaletna voda|krema za lice|kozmetika za lice|maski\b|aksesori\b|posluzuvanje|skladiranje|sad za'),
    ("care", r'sampon|regenerator|pasta za zab|pasti za zab|cetki za zab|kozmetika za usta|sapun|gel za tus|kupki|tusiranje|\bdeo\b|deo sprej|deo rolon|dezodor|deodorant|zilet|bricenj|bricalk|vlosk|tampon|zenska nega|higiensk|kremi za race|losion|kozmetika za telo|kozmetika za glava|lak,pena|proizvodi za zdravo telo'),
    ("household", r'deterg|omeknuv|softening|sredstv|sretstv|toaletna hartija|hartien|salfet|maramic|sunger|krpi|vreki|folij|ozoner|osvezuv|brisac|abraziv|prasoci za peren|prasaci|za perenje|tableti/kapsuli za obleka|vc blok|metli|cistenje|domakinski proizvodi|pomosni predmeti'),
    ("baby", r'pelen|bebi|bebe|bebinja|beb\b|kasick|detski kasi|kasi za deca|za deca|baby'),
    ("pets", r'kucinj|kuce\b|macki|mace\b|zivotni|milenic|\bpet\b|dog food|cat food|animal'),
    ("alcohol", r'\bvino\b|vina\b|\bpivo\b|piva\b|zestok|alkohol|rakij|viski|\bdzin\b|liker|\bwine\b|\bbeer\b|vodka|votka|konjak|brendi|vermut'),
    ("water", r'\bvoda\b|mineraln|\bwater\b'),
    ("soft", r'gazir|\bsok|sokov|sokcinj|dzus|pijalo|pijal\.|napit|nektar|sirup|cedevit|ladni caev|leden caj|laden caj|energetsk|tetrapak|bezalk|juice|soft drink|lemonade'),
    ("coffeeTea", r'kafe|kafinj|\bcaj\b|caevi|kakao|kapucin|frape|makijato|coffee|\btea\b'),
    ("iceCream", r'sladoled|ice cream|korneti,stap'),
    ("sweets", r'cokolad|bonbon|bomboni|kolac|kolaci|biskvit|piskot|napolit|oblandi|keks|vafl|tort|rolat|kroasan|konditor|alva|lokum|mastiki za dzvak|drazei|medenjac|desert|krem banan|cake|chocolate|candy|sweet|eurokrem|strudl'),
    ("snacks", r'grisin|cips|smoki|flips|solenk|perec|kreker|gricki|pukank|apetisan|snek|brusketi|kubeti|chips|snack|kikiriki|semenk|suvo ovosje|jatki|lesnic'),
    ("deli", r'pastet|salam|sunk|kolbas|virsl|suvomesn|cadeni|narezoc|kulen|cajni|sausage|slices|ham\b|mortadel|delikates|prsut|slanin'),
    ("meat", r'\bmeso\b|meso,|pilesk|pilsk|svinsk|govedsk|jagnesk|bataci|stek|mleveno|meleno meso|\bmeat\b|chicken|pork|beef'),
    ("fish", r'\bribi?\b|riba|ribni|morski|tuna|tunjev|sardin|skusa|losos|\bfish\b|seafood'),
    ("cheese", r'sirenj|kaskaval|\bsir\b|ajdamer|zdenk|topeno|cheese'),
    ("dairy", r'\bmleko\b|mlecn|jogurt|kefir|ajran|pavlak|puter|margarin|kajmak|maslo za|\bmilk\b|yog|dairy|butter'),
    ("eggs", r'\bjajca\b'),
    ("bread", r'\bleb\b|pecivo|peciva|kifl|tost|\bbread\b|lepinj|pita\b'),
    ("pastry", r'piti|burek|lisnat|strudl|kori\b|testo|pastry'),
    ("frozen", r'smrzn|zamrzn|frozen|ledeni'),
    ("produce", r'ovosje|zelencuk|fruit|vegetable|svezo|sveze'),
    ("preserved", r'zimnic|ajvar|turs|kornison|konzerv|maslink|domatno pire|prigotven|vlozen|pindzur|marinad'),
    ("sauces", r'\bsos|sosovi|kecap|majonez|senf|zacin|vegeta|supa|supi|kocki za|biber|cimet|kim\b|ocet|instant hrana|gotovi jadenja|spice|sauce|condiment|soup'),
    ("spreads", r'\bmed\b|marmalad|dzem|namaz|tahan|krem\b|kremovi|spread|honey|jam\b'),
    ("grains", r'testenin|makaron|spaget|\boriz|nudl|zitar|kornfleks|musli|pasta\b|tortel|lazanj|njoki|grains|cereal|rice'),
    ("baking", r'brasno|seker|kvas|pudin|prasoci|vanil|v\.sek|aroma|flour|sugar|baking|sweeteners|prelivi'),
    ("oil", r'maslo\b|maslinovo|\bocet|\boil\b'),
]
CATS = [(g, re.compile(r)) for g, r in CAT_RULES]

def cat_groups(cat_text):
    """Groups a shelf category belongs to; empty set = unknown (no check)."""
    t = (cat_text or "").strip()
    if not t or t in ("/", "-"): return set()
    out = {g for g, rx in CATS if rx.search(t)}
    # a fruit yogurt shelf is dairy, a dried-fruit shelf is snacks, a frozen-veg shelf is frozen: drop the weaker match
    if "produce" in out and out & {"dairy", "snacks", "frozen", "preserved", "soft", "sweets", "baby", "spreads"}: out.discard("produce")
    if "meat" in out and "deli" in out: out.discard("meat")
    return out

GROUP_TYPES = {
    "produce": "apples bananas oranges mandarins lemons limes grapes pears peaches strawberries watermelon kiwi plums mango avocado tomatoes cucumbers peppers hotPeppers potatoes sweetPotato onions springOnion garlic ginger carrots cabbage lettuce zucchini eggplant spinach broccoli cauliflower mushrooms celery leek beetroot pumpkin parsley dill freshHerbs",
    "meat": "wholeChicken chickenBreast chickenThighs chickenWings mince beefMince porkNeck porkChops beefStew steak lamb",
    "deli": "sausages sujuk ham bacon salami chickenHam pastrami",
    "fish": "trout salmon seaBream tuna sardines hake fishSticks shrimp squid",
    "dairy": "milk yogurt kefir ayran sourCream cream kajmak butter margarine",
    "cheese": "whiteCheese kashkaval mozzarella parmesan cottageCheese creamCheese",
    "eggs": "eggs",
    "bread": "whiteBread wholeBread toastBread rolls pitaBread tortillas",
    "pastry": "burek croissant filo",
    "baking": "flour cornmeal sugar salt yeast bakingPowder vanillaSugar cocoa puddingMix",
    "grains": "rice pasta noodles riceNoodles bulgur couscous oats cornflakes muesli breadcrumbs",
    "oil": "oil oliveOil vinegar",
    "preserved": "ajvar tomatoSauce tomatoPaste cannedTomatoes beans dryBeans lentils chickpeas corn olives pickles sourCabbage vineLeaves pickledVeg coconutMilk",
    "sauces": "tomatoSauce tomatoPaste cannedTomatoes ajvar mayonnaise ketchup mustard soySauce curryPowder seasoning paprika blackPepper cinnamon oregano driedMint cumin salt",
    "spreads": "honey jam chocoSpread peanutButter tahini",
    "snacks": "crisps flips sticks popcorn walnuts almonds peanuts raisins dates",
    "sweets": "chocoSpread chocolate biscuits wafers cakes candy gum halva croissant puddingMix",
    "iceCream": "iceCream",
    "frozen": "peas mixedVeg frozenSpinach hake fishSticks shrimp squid fries pizza iceCream burek wholeChicken chickenBreast chickenThighs chickenWings mince beefMince",
    "coffeeTea": "coffee instantCoffee tea cocoa icedTea",
    "water": "water sparklingWater mineral",
    "soft": "cola orangeSoda lemonSoda tonic orangeJuice appleJuice fruitJuice icedTea energy",
    "alcohol": "beer redWine whiteWine roseWine rakija whisky vodka gin liqueur",
    "household": "laundry softener dishSoap dishTabs cleaner bleach toiletPaper kitchenRoll napkins binBags sponges foil babyWipes",
    "care": "shampoo conditioner showerGel soap toothpaste toothbrush deodorant razors pads handCream babyWipes",
    "baby": "diapers babyWipes babyFood babyFormula",
    "pets": "catFood dogFood",
    "nonfood": "",
}
TYPE_GROUPS = {}
for grp, ts in GROUP_TYPES.items():
    for t in ts.split(): TYPE_GROUPS.setdefault(t, set()).add(grp)

def fits(g, cat_text):
    """Does product type g fit the chain's shelf category? Unknown shelves are accepted."""
    cg = cat_groups(cat_text)
    if not cg: return True
    return bool(TYPE_GROUPS.get(g, set()) & cg)

# Words in a NAME that show a product is processed or something else entirely, for every product type that is
# sold fresh (fruit, vegetables, fresh meat). Catches what shelf categories can't (chains without categories).
NOT_FRESH_PRODUCE = re.compile(
    r'pasteta|pasht|zacin|maggi|\bmagi\b|ideja za|vegeta|kocka|kocki|supa|corba|\bsos\b|kecap|kacap|ketchup|majonez|'
    r'cips|smoki|pringles|krekeri|grick|stapc|flips|\bvkus|aroma|'
    r'turs|kisel|marinir|vlozen|konzerv|teglic|tegla|dojpak|doypack|barena|filet[ia]?\b|pecen|ajvar|pindzur|lutenic|'
    r'pire|melen|mlen|cel[ia]\b|panir|pohov|susen|\bsuv[aieo]?\b|vo prav|prasok|granul|makalo|'
    r'banick|burek|pita\b|piti\b|kolpid|pecivo|pica|pizza|lazanj|'
    r'zamrz|smrzn|frozen|pomfrit|wedges|vedzis|golden long|mekejn|mccain|aviko|fritoso|'
    r'dzem|marmelad|kompot|\bsok\b|nektar|dzus|sirup|\bcaj\b|jogurt|kasick|bebi|hipp|\bhip\b|nutrino|\blino\b|'
    r'naturalis|cokolad|bonbon|gumen|keks|biskv|kolac|sladoled|\bkrem\b|namaz|harin|skusa|sardin|tuna|\bmace\b|macki|kuce|pedigr|friski')
NOT_FRESH_MEAT = re.compile(
    r'pasteta|pasht|zacin|maggi|\bmagi\b|ideja za|vegeta|kocka|supa|corba|\bsos\b|\bvkus|aroma|cips|smoki|'
    r'mace|macki|macka|kuce|kucinja|pedigr|friski|whiskas|viskas|felix|feliks|purina|\bcat\b|\bdog\b|adult|junior|hrana za|'
    r'slajs|slice|sunk|salam|virsl|kolbas|cadena?|cadeni|dimlen|narezo|pastrm|'
    r'nagets|pohovan|panir|kiev|topcinja|cufte|burger|pljeskav|kebap|cevap|'
    r'vo ocet|vo maslo|konzerv|pecen|grilovan|so pomfrit|lazanj|pica|pita|burek|sendvic|bebi|kasick')
FRESH_TYPES = set(GROUP_TYPES["produce"].split()) | set(GROUP_TYPES["meat"].split())

# Fresh food has no brand, except real producers of fresh food
FRESH_BRANDS = {'perutnina', 'cekin', 'koka', 'pivka', 'podgorka', 'zlatiborac', 'mein', 'soleta', 'pekabesko', 'neoplanta', 'grozdanovski', 'grozdanoski', 'pelagonija', 'seara', 'agrokor', 'zito', 'swisslion', 'veze', 'vezesari'}
