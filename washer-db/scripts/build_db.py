import json,os,re,csv,collections
S='../s'; SH='../shops'
ov=json.load(open(f'{SH}/ov.json')); feat=json.load(open('ov_feat.json'))
for i,o in enumerate(ov): o['type']=feat['type'][i]; o['dose'],o['steam'],o['wifi']=feat['feat'][i]
rows=json.load(open(f'{SH}/shop_rows.json'))
cand=json.load(open('candidates.json'))
aeg_pnc={}
for f in [f'{S}/aeg/list.txt','aeg_list.txt']:
    for l in open(f):
        a=l.split()
        if len(a)==2: aeg_pnc[a[0]]=a[1]
def num(x):
    try: return float(str(x).replace(' ','').replace(',','.'))
    except: return None
def yn(v):
    if v is None: return 'Not listed'
    v=str(v)
    if v.startswith('Yes') or v=='Ja': return 'Yes'
    if v.startswith('No') or v=='Nei': return 'No'
    return v
def fx(t):
    for enc in ('cp1252','latin-1'):
        try: return t.encode(enc).decode('utf-8')
        except Exception: pass
    return t
# ---------- BOM loaders ----------
def load_bsh(code):
    for f in [f'{S}/out/{code}.json',f'raw/bsh/{code}.json']:
        if os.path.exists(f) and os.path.getsize(f)>0:
            try: d=json.loads(open(f).read().strip().splitlines()[-1])
            except Exception: continue
            if not d.get('bom'): return {'status':'Not found','note':d.get('error') or 'no parts list','key':d.get('enr'),'url':d.get('url')}
            items=d.get('items',{}); parts=[]
            for b in d['bom']:
                it=items.get(b['id'],{}) or {}
                parts.append({'no':b['id'],'pos':b['pos'],'name':it.get('name') or '','price':it.get('price'),'group':b['pos'][:2]})
            return {'status':'Found','catalogue':'BSH spare-parts shop','key':d.get('enr'),'url':d.get('url'),'parts':parts,'variants':d.get('variants')}
    return {'status':'Not checked'}
def load_aeg(code):
    for f in [f'{S}/aeg/out/{code}.json',f'raw/aeg/{code}.json']:
        if os.path.exists(f) and os.path.getsize(f)>0:
            try: d=json.loads(open(f).read().strip().splitlines()[-1])
            except Exception: continue
            parts=[]
            for s in d.get('sections',[]):
                for p in s['parts']:
                    if p.get('no'): parts.append({'no':p['no'],'pos':p['pos'],'name':fx(p['name'] or ''),'price':p.get('price'),'group':fx(s['text'])})
            if not parts: return {'status':'Not found','note':'PNC gives no parts list in shop.aeg.no','key':d.get('pnc'),'url':d.get('url')}
            return {'status':'Found','catalogue':'AEG spare-parts shop (shop.aeg.no)','key':d.get('pnc'),'url':d.get('url'),'parts':parts}
    if code not in aeg_pnc: return {'status':'Not found','note':'PNC not found (not on aeg.no/aeg.se or Power)'}
    return {'status':'Not checked'}
def load_miele(code):
    f=f'raw/miele/{code}.json'
    if not os.path.exists(f): return {'status':'Not checked'}
    d=json.load(open(f))
    if d.get('error') or not d.get('groups'): return {'status':'Not found','note':d.get('error') or 'no parts list'}
    parts=[]; tubtext=None
    for g in d['groups']:
        for i,p in enumerate(g['parts']):
            if g['num']=='040' and p['type']=='TextPosition' and p['name'] and tubtext is None and 'beholder' in p['name'].lower():
                nxt=g['parts'][i+1]['name'] if i+1<len(g['parts']) else ''
                tubtext=p['name']+(' ('+nxt+')' if 'reservedel' in (nxt or '') else '')
            for no in (p['no'] or '').split(','):
                if no: parts.append({'no':no,'pos':p['fig'],'name':(p['name'] or '').lstrip('-'),'price':p['price'],'group':g['num']+' '+g['desc']})
    return {'status':'Found','catalogue':'Miele spare-parts catalogue (MSD)','key':f"{d['device']['modelName']} (id {d['device']['id']})",'url':d['url'],'parts':parts,'tubtext':tubtext}
def load(brand,code):
    return load_bsh(code) if brand in('Bosch','Siemens') else load_aeg(code) if brand=='AEG' else load_miele(code)
# ---------- roles & mechanical subset ----------
def mech(brand,p):
    if brand in('Bosch','Siemens'): return p['pos'].startswith('03')
    if brand=='AEG': return p['group'].startswith('Funksjonelle') or (p['pos'].startswith('504') and p['name'].lower().startswith('motor,'))
    return p['group'][:3] in ('040','130')
def roles(brand,b):
    R=collections.defaultdict(list)
    for p in b['parts']:
        n=p['name']; nl=n.lower()
        if brand in('Bosch','Siemens'):
            if not p['pos'].startswith('03'): continue
            if n in('Såpebeholder','Komplett oscillasjonssystem','Kar front','Bagkar','Kar'): R['Outer tub'].append(p)
            elif n=='Motor': R['Motor'].append(p)
            elif n=='Trommel': R['Drum'].append(p)
            elif n in('Støtdemper','Demper'): R['Shock absorber'].append(p)
        elif brand=='AEG':
            if p['group'].startswith('Funksjonelle') and p['pos']=='600': R['Outer tub (welded with drum)'].append(p)
            elif p['pos'].startswith('504') and nl.startswith('motor,'): R['Motor'].append(p)
            elif 'demper' in nl: R['Shock absorber'].append(p)
        else:
            g=p['group'][:3]
            if g=='130' and 'motor' in nl and not any(x in nl for x in ('skrue','hylse','brakett','kabel')): R['Motor'].append(p)
            elif g=='040' and nl.startswith('friksjonsdemper'): R['Shock absorber'].append(p)
            elif g=='040' and nl.startswith('vaskebeholder'): R['Outer tub'].append(p)
            elif nl.startswith('trommel') and 'belysning' not in nl and g in('040','030'): R['Drum'].append(p)
    if brand=='Miele' and not R['Outer tub'] and b.get('tubtext'): R['Outer tub'].append({'no':'','name':b['tubtext'],'pos':'10','price':''})
    # de-duplicate
    for k in R:
        seen=set(); R[k]=[p for p in R[k] if not (p['no'] in seen or seen.add(p['no']))]
    return R
# ---------- models ----------
TODAY='9 Nov 2026'
spec_elk={r['code']:r for r in rows if r['shop']=='Elkjøp'}
models={}
for o in ov:
    models[o['code']]=dict(code=o['code'],brand=o['brand'],name=o['name'],type=o['type'],in_ov='Yes',cap=o['cap'],rpm=o['rpm'],kwh=o['kwh'],db=o['db'],w=o['w'],wsrc='Manufacturer (brand tab)',
        dose=yn(o['dose']),steam=yn(o['steam']),wifi=yn(o['wifi']),shops=set(),fsrc='Brand tab (manufacturer)')
for r in rows:
    m=models.get(r['code'])
    if m is None:
        e=spec_elk.get(r['code'],r)
        typ='Washer-dryer' if '/kombinert' in r['url'] or 'kombinert-vasktoerk' in r['url'] else 'Washer'
        m=models[r['code']]=dict(code=r['code'],brand=r['brand'],name='',type=typ,in_ov='No',cap=e['cap'],rpm=e['rpm'] or r['rpm'],kwh=e['kwh'],db=e['db'],w=e['w'],wsrc='Elkjøp' if e['w'] else '',
            dose=yn(e['dose']) if e['shop']=='Elkjøp' else 'Not listed',steam=yn(e['steam']) if e['shop']=='Elkjøp' else 'Not listed',wifi=yn(e['wifi']) if e['shop']=='Elkjøp' else 'Not listed',shops=set(),fsrc='Elkjøp spec table' if e['shop']=='Elkjøp' else 'Not listed')
    m['shops'].add(r['shop'])
need=set(o['code'] for o in ov)|set(cand)
boms={c:load(models[c]['brand'],c) for c in need}
for c,b in boms.items():
    if b['status']=='Found' and len([p for p in b['parts'] if mech(models[c]['brand'],p)])<5:
        b['status']='Partial'; b['note']='mechanical section missing from the parts list'
R={c:(roles(models[c]['brand'],b) if b['status'] in ('Found','Partial') else {}) for c,b in boms.items()}
# ---------- matches ----------
def labeq(a,b):
    if a['cap'] is None or b['cap'] is None: return 'Not listed'
    if a['cap']!=b['cap']: return 'No (capacity)'
    if a['rpm'] and b['rpm'] and abs(a['rpm']-b['rpm'])>60: return 'No (spin speed)'
    if a['kwh'] is None or b['kwh'] is None: return 'Partly (kg/rpm match, rest not listed)'
    return 'Yes' if (a['kwh']==b['kwh'] and a['db']==b['db']) else 'No (kWh or noise)'
def setof(c,mechonly):
    b=boms[c]; br=models[c]['brand']
    return {p['no'] for p in b['parts'] if (mech(br,p) if mechonly else True)}
def rolenos(c,role):
    return {p['no'] for p in R[c].get(role,[]) if p['no']}
def tubrole(c):
    return next((k for k in R[c] if k.startswith('Outer tub')),None)
matches=[]
for c,ovs in sorted(cand.items()):
    for oc in ovs:
        A=models[oc]; B=models[c]; ba=boms[oc]; bb=boms[c]
        if ('dryer' in A['type'].lower())!=('dryer' in B['type'].lower()): continue
        m=dict(ov=oc,ovname=A['name'],cand=c,brand=A['brand'],shops=', '.join(sorted(B['shops'])),label=labeq(A,B))
        fd=[]
        for k,lab in (('dose','Auto-dosing'),('steam','Steam'),('wifi','Wi-Fi')):
            if A[k]!=B[k]: fd.append(f"{lab}: {A['code']} {A[k]}, {c} {B[k]}")
        m['featdiff']='; '.join(fd) or ('None' if all(B[k]!='Not listed' for k in ('dose','steam','wifi')) else 'None found (some not listed)')
        if ba['status']!='Found' or bb['status']!='Found':
            m.update(tub='Not checked',motor='Not checked',mech='',allp='',verdict='Parts not checked: '+(f"{oc}: {ba.get('note') or ba['status']}" if ba['status']!='Found' else f"{c}: {bb.get('note') or bb['status']}"))
            m['evidence']=''
        else:
            ma,mb=setof(oc,True),setof(c,True); aa,ab=setof(oc,False),setof(c,False)
            m['mech']=f"{len(ma&mb)} of {len(ma|mb)} ({round(100*len(ma&mb)/max(1,len(ma|mb)))}%)"
            m['allp']=f"{len(aa&ab)} of {len(aa|ab)} ({round(100*len(aa&ab)/max(1,len(aa|ab)))}%)"
            mechpct=len(ma&mb)/max(1,len(ma|mb))
            tr=tubrole(oc) or tubrole(c)
            ta,tb=(rolenos(oc,tr),rolenos(c,tr)) if tr else (set(),set())
            if ta and tb: tub='Same' if ta&tb else 'Different'
            elif A['brand']=='Miele' and tr: tub='No spare part (both)' if (not ta and not tb) else 'Different'
            else: tub='Not listed'
            pa,pb=rolenos(oc,'Motor'),rolenos(c,'Motor')
            mot='Same' if (pa and pb and pa&pb) else 'Different' if (pa and pb) else 'Not listed'
            m['tub']=tub+(f" ({', '.join(sorted(ta|tb))})" if (ta|tb) else ''); m['motor']=mot+(f" ({', '.join(sorted(pa|pb))})" if (pa|pb) else '')
            if tub=='Different' and mechpct>=0.75: v='Same platform, outer tub part number differs'
            elif tub=='Different': v='Different machine (outer tub differs)'
            elif mot=='Different': v='Different machine (motor differs)'
            elif mechpct>=0.8: v='Same mechanics (parts verified)'
            elif mechpct>=0.5: v='Same platform, some mechanical parts differ'
            else: v='Different machine (most mechanical parts differ)'
            m['verdict']=v
            m['evidence']=f"{oc}: {ba['catalogue']}, {ba['key']}; {c}: {bb['key']}"
        matches.append(m)
json.dump({'models':{k:{**v,'shops':sorted(v['shops'])} for k,v in models.items()},'matches':matches},open('db_out.json','w'),ensure_ascii=False,default=str)
print(len(matches)); print(collections.Counter(m['verdict'].split(':')[0] for m in matches))
