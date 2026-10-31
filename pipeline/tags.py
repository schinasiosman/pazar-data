"""Variant words (flavour, kind, form) found in a product name, as language-neutral keys.
The app shows them in the user's language: 'Pionir' + hazelnut + chocolate + 100 g, instead of a transliterated name."""
import re

TAGS = [  # (key, regex on the normalised Latin name). Order = display order.
    ("milkChoc", r'mlecn[ao] cokol|milk choc'), ("darkChoc", r'crn[ao] cokol|dark|bitter'), ("whiteChoc", r'bel[ao] cokol|white choc|\bbelo\b.*coko'),
    ("hazelnut", r'lesnik|lesnic|hazelnut|ljesnjak|fstak|pistac'), ("almond", r'badem|almond'), ("peanut", r'kikiriki|peanut'), ("coconut", r'kokos|coconut'),
    ("strawberry", r'jagod|strawberr'), ("raspberry", r'malin|raspberr'), ("cherry", r'visn|cresh|cherry'), ("peach", r'praska|praskv|breskv|peach'),
    ("apricot", r'kajsij|apricot'), ("apple", r'jabolk|jabuk|apple'), ("orange", r'portokal|orange|oranz'), ("lemon", r'limon|lemon'),
    ("banana", r'banan'), ("forestFruit", r'sumsk|forest|borovnic|blueberr'), ("multiFruit", r'multi ?vit|multivitamin|tropik|tropic|multi fruit|multifruit'),
    ("vanilla", r'vanil'), ("caramel", r'karamel|caramel'), ("cocoa", r'kakao|cocoa'), ("coffeeFl", r'\bkafe\b|coffee|kapucin'), ("honeyFl", r'\bso med\b|\bmed i\b|honey'),
    ("cheeseFl", r'sirenj|kaskaval|cheese|cedar|cheddar'), ("paprikaFl", r'paprika|piperk'), ("saltFl", r'\bsolen|\bsalt|\bsol\b'), ("sourCreamOnion", r'pavlak.*kromid|kromid.*pavlak|sour cream'),
    ("spicy", r'\blut[aio]?\b|\bljut|\bhot\b|spicy|chili|cili'), ("mint", r'\bnane\b|menta|mint'),
    ("light", r'\blight|\blajt|\blite\b|\bfit\b'), ("sugarFree", r'bez seker|bez secer|bez dodaden seker|sugar free|\bzero\b|no sugar'), ("lactoseFree", r'bez laktoz|lactose free'),
    ("glutenFree", r'bez gluten|gluten free'), ("wholegrain", r'integral|polnozrn|wholegrain|whole grain|razen|\bovesen\b'), ("organic", r'organsk|\bbio\b|organic'),
    ("smoked", r'cadeni|cadena|caden\b|dimlen|smoked'), ("sliced", r'slajs|slice|secen[ao]?\b|narezan'), ("frozenT", r'zamrz|smrzn|frozen'), ("freshT", r'\bsvez|\bfresh'),
    ("cow", r'kravj|kravsk'), ("sheep", r'ovcj|ovcov'), ("goat", r'kozj'), ("pork", r'svinsk'), ("beefT", r'govedsk|juneck'), ("chickenT", r'pilesk|pileski|pilsk'), ("turkey", r'misirk|\bcurk|\bcurec'),
    ("inOil", r'vo maslo|u ulju|in oil'), ("inWater", r'vo sopstven|vo voda|in water|vlastitom'),
    ("sparkling", r'(?<!ne)gazir'), ("still", r'negazir'),
    ("spaghetti", r'spaget'), ("penne", r'\bpene\b|penne'), ("fusilli", r'fusil'), ("macaroni", r'makaron'), ("tagliatelle", r'taljatel|tagliatel'), ("basmati", r'basmati'),
    ("mini", r'\bmini\b'), ("classic", r'klasi[ck]|classic|original'), ("family", r'famil'), ("multipack", r'multipak|multipack|\bmpak\b'),
]
TAGX = [(k, re.compile(r)) for k, r in TAGS]
PRODUCE_T = {"apples","bananas","oranges","mandarins","lemons","limes","grapes","pears","peaches","strawberries","watermelon","kiwi","plums","mango","avocado","tomatoes","cucumbers","peppers","hotPeppers","potatoes","sweetPotato","onions","springOnion","garlic","ginger","carrots","cabbage","lettuce","zucchini","eggplant","spinach","broccoli","cauliflower","mushrooms","celery","leek","beetroot","pumpkin","parsley","dill","freshHerbs"}
# kinds of fresh fruit and vegetables named in the price lists (pink tomatoes, babura peppers, Golden Delicious apples…)
VARIETY = [("pinkT", r'rozev|\broze\b|pink'), ("cherryT", r'\bcheri\b|\bceri\b|cherry'), ("babura", r'babur'), ("kapija", r'kapij'), ("horn", r'\brog\b|rogov'),
    ("redT", r'\bcrven[aiueo]?\b'), ("yellowT", r'\bzolt[aiueo]?\b'), ("greenT", r'\bzelen[aiueo]?\b'), ("whiteT", r'\bbel[aioe]?\b'), ("blackT", r'\bcrn[aoie]?\b'),
    ("youngT", r'\bmlad[aiueo]?\b'), ("iceberg", r'ajzberg|iceberg'), ("rocket", r'rukola|rokola|rucola'), ("goldenDel", r'zlaten delis|golden'), ("idared", r'ajdared|idared'),
    ("granny", r'greni ?smit|granny'), ("gala", r'\bgala\b'), ("fuji", r'fudzi|\bfuji'), ("seedless", r'bez semk|besemen'), ("bunch", r'kitk|vrsk')]
VARX = [(k, re.compile(r)) for k, r in VARIETY]
def variety_of(n):
    return [k for k, rx in VARX if rx.search(n)][:2]

def tags_of(n, g=None, fat=''):
    out = [k for k, rx in TAGX if rx.search(n)]
    # a flavour that is the product itself is not a variant (an 'apple' tag on apple juice, 'chicken' on chicken)
    same = {"appleJuice": "apple", "orangeJuice": "orange", "chocolate": "cocoa", "cocoa": "cocoa", "honey": "honeyFl", "coffee": "coffeeFl", "instantCoffee": "coffeeFl",
            "peanutButter": "peanut", "peanuts": "peanut", "almonds": "almond", "lemons": "lemon", "oranges": "orange", "apples": "apple", "bananas": "banana",
            "strawberries": "strawberry", "peaches": "peach", "pork": "pork", "porkNeck": "pork", "porkChops": "pork", "beefStew": "beefT", "beefMince": "beefT", "steak": "beefT",
            "chickenBreast": "chickenT", "wholeChicken": "chickenT", "chickenThighs": "chickenT", "chickenWings": "chickenT", "chickenHam": "chickenT", "pasta": None,
            "sparklingWater": "sparkling", "water": "still", "mineral": "sparkling", "paprika": "paprikaFl", "peppers": "paprikaFl", "hotPeppers": "paprikaFl", "cheese": "cheeseFl", "kashkaval": "cheeseFl", "whiteCheese": "cheeseFl", "lemonSoda": "lemon", "orangeSoda": "orange", "tonic": "lemon"}
    if g in same and same[g] in out: out.remove(same[g])
    if "milkChoc" in out and "cocoa" in out: out.remove("cocoa")
    if g in PRODUCE_T and "freshT" in out: out.remove("freshT")
    if fat: out.insert(0, "fat:" + fat)
    return out[:4]
