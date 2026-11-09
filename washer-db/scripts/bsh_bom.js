// Read-only: no login, no cart. Usage: node full.js brand model [fd]
const { chromium } = require('playwright');
(async()=>{
 const [brand,model,fdArg]=process.argv.slice(2);
 const host= brand==='Bosch' ? 'https://www.bosch-home.no' : 'https://www.siemens-home.bsh-group.com';
 const pfx = brand==='Bosch' ? '/no' : '/no/no';
 const B = brand.toUpperCase();
 const out={brand,model};
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1400,height:1000}});
 let gqlHash=null; p.on('request',r=>{const m=r.url().match(/operationName=ProductItems.*sha256Hash%22%3A%22([0-9a-f]{64})/); if(m) gqlHash=m[1];});
 try{
  const sp = brand==='Bosch' ? host+'/produkter/reservedeler' : host+'/no/no';
  await p.goto(sp,{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(2500);
  const btn=p.getByRole('button',{name:'Avvis alle'}); if(await btn.count()) await btn.first().click().catch(()=>{});
  const sugg=await p.evaluate(async([host,model])=>{ const r=await fetch(`${host}/ajax/sparepart/advanced/enumbersearch/suggestresult?eg=&cluster=&tab=%2FTabs%3Dsection-spareparts%2F&vibki=${model}&sourceUrl=`); return r.ok? (await r.json()).map(x=>x.value):['HTTP '+r.status]; },[host,model]).catch(e=>['ERR '+e.message]);
  out.variants=sugg;
  const fd = fdArg || (sugg.filter(v=>/\//.test(v) && v.startsWith(model+'/')).slice(-1)[0]);
  out.enr=fd;
  const url=`${host}${pfx}/spare-parts-list/${fd.replace('/','-')}`; out.url=url;
  const r=await p.goto(url,{waitUntil:'domcontentloaded',timeout:60000}); out.status=r.status();
  await p.waitForTimeout(3000);
  const btn2=p.getByRole('button',{name:'Avvis alle'}); if(await btn2.count()) await btn2.first().click().catch(()=>{});
  for(let i=0;i<8;i++){ await p.mouse.wheel(0,1200); await p.waitForTimeout(300);} await p.waitForTimeout(2500);
  const html=(await p.content()).replace(/\\"/g,'"');
  const bom=[...html.matchAll(/"productId":"(\d+)","positionNumber":"(\d+)"/g)].map(m=>({id:m[1],pos:m[2]}));
  const seen=new Set(); out.bom=bom.filter(x=>{const k=x.id+x.pos; if(seen.has(k)) return false; seen.add(k); return true;});
  out.gallery=[...new Set([...html.matchAll(/"id":"(\d+_aet_\d+_[a-z]_\d+)","url":"([^"]+)","positionNumber":"(\d+)"/g)].map(m=>m[3]+' '+m[2]))];
  out.total=((await p.innerText('body')).match(/av (\d+) reservedeler/)||[])[1];
  if(!gqlHash) gqlHash='512884bf8b69434c773e3b15924e2e2858aa993f4465f67db3002497979927f4'; out.hash=gqlHash;
  const ids=[...new Set(out.bom.filter(x=>x.pos.startsWith("03")).map(x=>x.id))];
  const items={};
  for(let i=0;i<ids.length;i+=8){
    const chunk=ids.slice(i,i+8); await p.waitForTimeout(6000);
    for(let attempt=0;attempt<3;attempt++){
    const res=await p.evaluate(async([host,chunk,hash,B])=>{
      const v=encodeURIComponent(JSON.stringify({productIds:chunk,includePromotion:true}));
      const e=encodeURIComponent(JSON.stringify({persistedQuery:{version:1,sha256Hash:hash},shop:{brand:B,country:'NO',language:'no',channel:'B2C',cas:true}}));
      const r=await fetch(`${host}/graphql?operationName=ProductItems&variables=${v}&extensions=${e}`,{headers:{'content-type':'application/json'}});
      return await r.text();
    },[host,chunk,gqlHash,B]);
    try{ for(const it of (JSON.parse(res).data||{}).productItems||[]){ if(!it||!it.product) continue;
      const pr=it.product; const succ=it.product.salesInformation&&it.product.salesInformation.successorItem;
      const name=(pr.header||[]).find(h=>h.level==2); const img=pr.assets&&pr.assets.images&&pr.assets.images[0];
      items[pr.id]={name:name&&name.value, price:it.price&&it.price.displayPrice&&it.price.displayPrice.amount, img:img&&img.id,
        succ: succ? {id:succ.product.id, name:((succ.product.header||[]).find(h=>h.level==2)||{}).value, price:succ.price&&succ.price.displayPrice&&succ.price.displayPrice.amount, img:succ.product.assets&&succ.product.assets.images&&succ.product.assets.images[0]&&succ.product.assets.images[0].id}:null};
    }
    if(/fetch limit/.test(res)) throw new Error('limit'); break; }catch(err){ out.gqlErr=(out.gqlErr||'')+' | '+String(err.message).slice(0,40); await p.waitForTimeout(8000); }
  }}
  out.items=items;
 }catch(e){ out.error=e.message.split('\n')[0]; }
 console.log(JSON.stringify(out));
 await b.close();
})();
