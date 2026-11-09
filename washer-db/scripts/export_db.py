import json,csv,os
exec(open('build_db.py').read())
def f(x): 
    if x is None or x=='': return 'Not listed'
    if isinstance(x,float) and x.is_integer(): return int(x)
    return x
REPO='https://github.com/martinbaklid/notes/blob/claude/brave-curie-0th52n/washer-db/'
# db_models: Overview models + candidates (the codes whose parts were checked)
mh=['Model code','Brand','Type','In Overview','Overview name','Sold at (Elkjøp/Power)','Capacity kg','Max spin rpm','kWh per 100 cycles','Spin noise dB','Weight kg','Weight source','Auto-dosing','Steam','Wi-Fi','Feature source','Parts catalogue','Parts lookup key (E-Nr / PNC / Miele model)','Parts list status','Parts in list','Mechanical parts in list','Parts page','Checked']
mrows=[mh]
for c in sorted(need,key=lambda c:(models[c]['brand'],c)):
    m=models[c]; b=boms[c]; br=m['brand']
    np=len(b.get('parts',[])); nm=len([p for p in b.get('parts',[]) if mech(br,p)])
    mrows.append([c,br,m['type'],m['in_ov'],m['name'] or '',', '.join(sorted(m['shops'])) or 'Not listed',f(m['cap']),f(m['rpm']),f(m['kwh']),f(m['db']),f(m['w']),m['wsrc'] or 'Not listed',m['dose'],m['steam'],m['wifi'],m['fsrc'],
        b.get('catalogue') or {'Bosch':'BSH spare-parts shop','Siemens':'BSH spare-parts shop','AEG':'AEG spare-parts shop (shop.aeg.no)','Miele':'Miele spare-parts catalogue (MSD)'}[br],
        b.get('key') or (aeg_pnc.get(c) if br=='AEG' else '') or 'Not found', b['status']+(f" ({b['note']})" if b.get('note') else ''), np or '', nm or '', b.get('url') or 'Not found', TODAY])
# db_key_parts
kh=['Model code','Brand','Role','Part number','Part name (as in catalogue)','Position','Price NOK (catalogue)']
krows=[kh]
for c in sorted(need,key=lambda c:(models[c]['brand'],c)):
    b=boms[c]
    if b['status'] not in ('Found','Partial'): continue
    for role in sorted(R[c]):
        for p in (R[c][role][:2] if role=='Shock absorber' else R[c][role]):
            krows.append([c,models[c]['brand'],role,p['no'] or '(no part number)',p['name'],p['pos'],(f(num(p['price'])) if num(p.get('price')) is not None else 'Not shown')])
# db_matches
xh=['Overview model','Overview name','Candidate code','Brand','Candidate sold at','Energy-label values equal?','Outer tub (part no.)','Motor (part no.)','Shared mechanical parts','Shared parts, whole list','Verdict','Feature differences','Checked']
xrows=[xh]+[[m['ov'],m['ovname'],m['cand'],m['brand'],m['shops'],m['label'],m['tub'],m['motor'],m['mech'] or 'Not checked',m['allp'] or 'Not checked',m['verdict'],m['featdiff'],TODAY] for m in sorted(matches,key=lambda m:(m['brand'],m['ov'],m['cand']))]
json.dump({'models':mrows,'keyparts':krows,'matches':xrows},open('sheet_payload.json','w'),ensure_ascii=False)
# repo CSVs
os.makedirs('repo/parts',exist_ok=True)
for c in need:
    b=boms[c]
    if b['status'] not in ('Found','Partial'): continue
    with open(f'repo/parts/{c}.csv','w',newline='') as fh:
        w=csv.writer(fh); w.writerow(['model_code','catalogue','lookup_key','group_or_section','position','part_number','part_name','price_nok','mechanical_subset','parts_page'])
        for p in b['parts']: w.writerow([c,b['catalogue'],b['key'],p['group'],p['pos'],p['no'],p['name'],p.get('price'),'yes' if mech(models[c]['brand'],p) else 'no',b['url']])
for name,data in (('db_models',mrows),('db_key_parts',krows),('db_matches',xrows)):
    with open(f'repo/{name}.csv','w',newline='') as fh: csv.writer(fh).writerows(data)
print(len(mrows),len(krows),len(xrows))
