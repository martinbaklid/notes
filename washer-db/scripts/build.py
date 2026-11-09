import json,re,collections
from fam import family
def code_of(brand,s):
    s=s.upper()
    if brand=='Miele':
        m=re.search(r'\b(W[A-Z]{1,2})\s?(\d{3,4})',s); return (m.group(1)+m.group(2)) if m else None
    if brand in('Bosch','Siemens'):
        m=re.search(r'\b(W[A-Z]{1,2}\d{2,5}[A-Z0-9]{2,7})\b',s); return m.group(1) if m else None
    m=re.search(r'\b(L[A-Z0-9]{6,10})\b',s); return m.group(1) if m else None
def num(x):
    if x in (None,''): return None
    m=re.search(r'\d+(?:[.,]\d+)?',str(x)); return float(m.group(0).replace(',','.')) if m else None
# Overview
ov=[]
for l in open('overview.tsv',encoding='utf-8'):
    b,name,cap,rpm,kwh,db,w=(l.rstrip('\n').split('\t')+['']*7)[:7]
    c=code_of(b,name)
    ov.append(dict(brand=b,name=name,code=c,fam=family(b,c),cap=num(cap),rpm=num(rpm),kwh=num(kwh),db=num(db),w=num(w)))
# shops
rows=[]
for l in open('elk_data.jsonl',encoding='utf-8'):
    r=json.loads(l); b=r.get('brand')
    if b not in('Bosch','Siemens','Miele','AEG') or not r.get('mpn'): continue
    s=r['specs']; c=code_of(b,r['mpn']) or code_of(b,r.get('name',''))
    if not c: continue
    av={'InStock':'In stock','SoldOut':'Sold out','InStoreOnly':'In store only'}.get(r.get('availability'),r.get('availability') or 'Not found')
    rows.append(dict(brand=b,code=c,shop='Elkjøp',name=r.get('name'),price=num(r.get('price')),stock=av,
        buyable=av in('In stock','In store only'),
        cap=num(s.get('Kapasitet vaskesyklus (kg)')),rpm=num(s.get('Sentrifugehastighet (o/min)')),kwh=num(s.get('Vektet energiforbruk vask (Kwh/100 sykluser)')),
        db=num(s.get('Luftbåren akustisk lydutslipp sentrifugeringsfase (dB)')),w=num(s.get('Vekt (kg)')),water=num(s.get('Vektet vannforbruk vaskesyklus (liter/syklus)')),
        eco=s.get('Syklusvarighet vaskesyklus (timer:minutter)'),steam=s.get('Dampfunksjon'),dose=s.get('Autodosering av vaskemiddel'),wifi=s.get('Wi-Fi'),url=r['url']))
stockmap={'aLotLeft':'In stock','GoodStock':'In stock','SomeLeft':'In stock (few)','FewLeft':'In stock (few)','WebStock':'In stock','CrossDockInStock':'In stock (supplier)',
 'ComingIn':'Coming in','ComingInUnconfirmed':'Coming in (unconfirmed)','OnDemand.Short':'On order'}
for p in json.load(open('power_all.json',encoding='utf-8')):
    if p['categoryName'] not in('Frontbetjent vaskemaskin','Kombinert vask/tørk'): continue
    b=p['manufacturerName']; c=code_of(b,p['title'])
    if not c: continue
    st=stockmap.get((p.get('webStockTextShort') or '').replace('Product.Stock.',''),(p.get('webStockTextShort') or '').replace('Product.Stock.',''))
    sa=p.get('salesArguments') or ''
    cap=num((re.search(r'(\d+(?:[.,]\d+)?)\s*kg',sa) or [None,None])[1]) if re.search(r'kg',sa) else None
    rpm=num((re.search(r'(\d{3,4})\s*(?:omdreininger|o/min|rpm)',sa) or [None,None])[1])
    rows.append(dict(brand=b,code=c,shop='Power',name=p['title'],price=p['price'],stock=st,buyable=st.startswith('In stock') or st.startswith('On order'),
        cap=cap,rpm=rpm,kwh=None,db=None,w=None,water=None,eco=None,steam=None,dose=None,wifi=None,url='https://www.power.no'+p['url']))
# Elkjøp specs reused for the same code at Power
spec_by_code={}
for r in rows:
    if r['shop']=='Elkjøp' and r['kwh']: spec_by_code[r['code']]=r
ov_by_code={o['code']:o for o in ov}
def relation(r):
    fam=family(r['brand'],r['code']); r['fam']=fam
    if r['code'] in ov_by_code: return ('Same code as Overview',ov_by_code[r['code']]['name'])
    mem=[o for o in ov if o['fam']==fam]
    if not mem: return ('Not in Overview (no family match)','')
    s=spec_by_code.get(r['code'],r)
    best=None
    for o in mem:
        if s['cap'] is not None and s['rpm'] is None and s['kwh'] is not None:
            rel='Probable variant (capacity, kWh and noise match; spin speed not listed)' if (s['cap']==o['cap'] and s['kwh']==o['kwh'] and s['db']==o['db']) else 'Same family (specs not listed)'
        elif s['cap'] is None or s['rpm'] is None:
            rel='Same family (specs not listed)'
        elif s['cap']!=o['cap'] or abs(s['rpm']-o['rpm'])>60:
            rel='Same family, different capacity or spin speed'
        elif s['kwh'] is None:
            rel='Probable variant (capacity and spin speed match; rest not listed)'
        elif s['kwh']==o['kwh'] and s['db']==o['db'] and (s['w'] is None or o['w'] is None or abs(s['w']-o['w'])<=2):
            rel='Same specs (likely shop-specific variant)'
        else:
            rel='Same kg and rpm, other specs differ'
        rank=['Same specs (likely shop-specific variant)','Probable variant (capacity, kWh and noise match; spin speed not listed)','Probable variant (capacity and spin speed match; rest not listed)','Same kg and rpm, other specs differ','Same family (specs not listed)','Same family, different capacity or spin speed'].index(rel)
        sim=sum(1 for a,b in zip(r['code'],o['code']) if a==b)
        if best is None or (rank,-sim)<(best[0],best[3]): best=(rank,rel,o['name'],-sim)
    return (best[1],best[2])
rows=[r for r in rows if r['price'] and 'brukt' not in r['url']]
for r in rows:
    e=r.get('eco')
    if e and ':' not in e and e.isdigit(): r['eco']=f"{int(e)//60}:{int(e)%60:02d}"
for r in rows:
    r['rel'],r['ovmodel']=relation(r)
json.dump(rows,open('shop_rows.json','w'),ensure_ascii=False)
json.dump(ov,open('ov.json','w'),ensure_ascii=False)
print(len(rows),collections.Counter(r['rel'] for r in rows))
for r in rows:
    if r['rel'] not in('Not in Overview (no family match)',): print(r['shop'],r['code'],r['price'],r['stock'],'|',r['rel'],'|',r['ovmodel'])
