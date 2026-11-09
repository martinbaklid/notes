import re,json,time,subprocess,sys,html as H
urls=[l.strip() for l in open('elk_brand.txt') if l.strip()]
out=open('elk_data.jsonl','a')
done=set()
try:
    for l in open('elk_data.jsonl'): done.add(json.loads(l)['url'])
except: pass
for u in urls:
    if u in done: continue
    r=subprocess.run(['curl','-sS','--max-time','40','-A','Mozilla/5.0 (X11; Linux x86_64) Chrome/124',u],capture_output=True)
    h=r.stdout.decode('utf-8','ignore')
    rec={'url':u}
    m=re.search(r'<script type="application/ld\+json"[^>]*>(\{"@context":"https://schema.org","@type":"Product".*?)</script>',h,re.S)
    if m:
        try:
            d=json.loads(m.group(1)); rec['name']=d.get('name'); rec['mpn']=d.get('mpn'); rec['gtin']=d.get('gtin'); rec['brand']=(d.get('brand') or {}).get('name')
            offs=d.get('offers') or []
            if isinstance(offs,dict): offs=offs.get('offers',[offs])
            for o in offs:
                if o.get('name')=='Standard Price': rec['price']=o.get('price'); rec['availability']=(o.get('availability') or '').split('/')[-1]
        except Exception as e: rec['err']=str(e)
    specs={}
    for dt,dd in re.findall(r'<dt>(.*?)</dt><dd[^>]*>(.*?)</dd>',h,re.S):
        k=H.unescape(re.sub(r'<[^>]+>','',dt)).strip(); v=H.unescape(re.sub(r'<[^>]+>',' ',dd)).strip()
        if k and k not in specs: specs[k]=re.sub(r'\s+',' ',v)
    rec['specs']=specs
    rec['status']=len(h)
    out.write(json.dumps(rec,ensure_ascii=False)+'\n'); out.flush()
    time.sleep(1.0)
