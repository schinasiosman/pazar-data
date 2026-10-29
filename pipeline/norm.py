import re,unicodedata
CYR={'а':'a','б':'b','в':'v','г':'g','д':'d','ѓ':'g','е':'e','ж':'z','з':'z','ѕ':'dz','и':'i','ј':'j','к':'k','л':'l','љ':'lj','м':'m','н':'n','њ':'nj','о':'o','п':'p','р':'r','с':'s','т':'t','ќ':'k','у':'u','ф':'f','х':'h','ц':'c','ч':'c','џ':'dz','ш':'s','ђ':'dj','ћ':'c','й':'j','ы':'i','э':'e','ю':'ju','я':'ja','ё':'e','ъ':'','ь':''}
def norm(s):
    s=str(s).lower()
    s=''.join(CYR.get(ch,ch) for ch in s)
    s=unicodedata.normalize('NFD',s); s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    s=s.replace('đ','dj')
    s=re.sub(r'[^a-z0-9.,%/x ]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()
UNIT={'kg':('g',1000),'kgr':('g',1000),'kilo':('g',1000),'gr':('g',1),'g':('g',1),'grm':('g',1),'l':('ml',1000),'lit':('ml',1000),'lt':('ml',1000),'ml':('ml',1),'cl':('ml',10),'dl':('ml',100)}
SZ=re.compile(r'(?:(\d{1,2})\s*[x*]\s*)?(\d+(?:[.,]\d+)?)\s*(kgr|kg|kilo|grm|gr|g|lit|lt|l|ml|cl|dl)(?![a-z])')
def size(n):
    """returns (base amount, base unit, multipack count) from a normalised name"""
    best=None
    for m in SZ.finditer(n):
        mult=int(m.group(1)) if m.group(1) else 1
        v=float(m.group(2).replace(',','.')); u,f=UNIT[m.group(3)]
        if u=='ml' and m.group(3)=='l' and v>=50: continue   # '500l' is noise
        raw=m.group(2)
        if m.group(3) in ('ml','gr','g','grm') and re.match(r'^\d[.,]\d{3}$',raw): v=v*1000    # '1.350ml' = 1350 ml
        elif m.group(3)=='ml' and v<10: v=v*1000                                                  # '0.33ml' means litres
        elif m.group(3) in ('gr','g','grm') and v<5 and ('.' in raw or ',' in raw): v=v*(100 if v<1 and len(re.split(r'[.,]',raw)[1])==2 else 1000)  # '0.400 gr' = 400 g, '0.40gr' = 40 g
        best=(round(v*f,3),u,mult)
    if best: return best
    m=re.search(r'(\d+)\s*(?:/1|kom|pc|pcs|parcinja|par)\b',n)
    if m: return (float(m.group(1)),'pcs',1)
    return None
