import json,re
exec(open('build_db.py').read().split('json.dump({')[0])
rows_shop=json.load(open('../shops/shop_rows.json'))
def offers(code):
    o=[r for r in rows_shop if r['code']==code and r['price']]
    return sorted(o,key=lambda r:(r['stock'].startswith('Sold'),r['price']))
SH={'Same mechanics (parts verified)':'same mechanics','Same platform, outer tub part number differs':'tub part no. differs','Same platform, some mechanical parts differ':'some mech. parts differ'}
def short(v):
    if v in SH: return SH[v]
    if v.startswith('Different'): return 'different machine'
    return 'parts not checked'
def realdiff(fd):
    parts=[p for p in fd.split('; ') if ':' in p and 'Not listed' not in p and 'Conflicting' not in p]
    return ', '.join(p.split(':')[0] for p in parts)
ovnames=[l.split('\t')[1] for l in open('../shops/overview.tsv',encoding='utf-8')]
byname={o['name']:o for o in ov}
out=[]
order=['same mechanics','tub part no. differs','some mech. parts differ','parts not checked','different machine']
for n in ovnames:
    oc=byname[n]['code']; ms=[m for m in matches if m['ov']==oc]
    items=[]
    for m in ms:
        of=offers(m['cand']); s=short(m['verdict'])
        price=f"{of[0]['shop']} {int(of[0]['price']):,}".replace(',',' ')+(' sold out' if of and of[0]['stock'].startswith('Sold') else '') if of else 'no price'
        d=realdiff(m['featdiff'])
        items.append((order.index(s), of[0]['price'] if of else 9e9, f"{m['cand']} ({s}; {price}"+(f"; differs: {d}" if d else '')+")", m, of, d))
    items.sort(key=lambda x:(x[0],x[1]))
    txt='; '.join(i[2] for i in items) or 'None found'
    best=[i for i in items if i[0]==0 and i[4] and not i[4][0]['stock'].startswith('Sold')]
    if best:
        b=best[0]; lab=f"{b[3]['cand']} ({b[4][0]['shop']}, {b[4][0]['stock'].lower()})"+(f" – differs: {b[5]}" if b[5] else (' – features not listed by the shop' if 'Not listed' in b[3]['featdiff'] else ' – no feature differences found'))
        out.append([txt,lab,int(b[4][0]['price'])])
    else:
        out.append([txt,'None found',''])
json.dump(out,open('ov_sisters.json','w'),ensure_ascii=False)
for n,r in zip(ovnames,out):
    if r[1]!='None found': print(n,'|',r[1],r[2])
