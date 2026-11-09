// Read-only: no login, no cart. Usage: node full.js MODEL PNC9
const { chromium } = require('playwright');
(async()=>{
 const [model,pnc9]=process.argv.slice(2);
 const out={model,pnc9,sections:[]};
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1400,height:1000}});
 const views=[]; p.on('response',async r=>{ if(r.request().method()==='POST' && /shop\.aeg\.no\/search/.test(r.url())){ try{ const t=await r.text(); const m=t.match(/^1:(\{.*\})\s*$/m); if(m){ const j=JSON.parse(m[1]); if(j.data&&j.data.views) views.push(...j.data.views); } }catch(e){} }});
 try{
  await p.goto('https://shop.aeg.no/',{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(4500);
  if(await p.locator('#onetrust-banner-sdk:visible').count()){ await p.locator('#onetrust-pc-btn-handler').click().catch(()=>{}); await p.waitForTimeout(1000); const c=p.locator('button.save-preference-btn-handler, .ot-pc-refuse-all-handler'); if(await c.count()) await c.first().click().catch(()=>{}); }
  await p.waitForTimeout(1000);
  const inp=p.locator('input[placeholder*="PNC"]:visible').first();
  await inp.click(); await inp.pressSequentially(pnc9,{delay:60}); await p.waitForTimeout(4000);
  out.variants=[...new Set(await p.$$eval('[role=option]',os=>os.map(o=>o.innerText.trim())))].filter(v=>/^\d{11}$/.test(v)).sort();
  const pnc=out.variants.length? out.variants[out.variants.length-1] : pnc9+'00';
  out.pnc=pnc; out.url='https://shop.aeg.no/search?pnc='+pnc;
  await p.goto(out.url,{waitUntil:'domcontentloaded',timeout:60000}); await p.waitForTimeout(5000);
  const html=(await p.content()).replace(/\\"/g,'"');
  { const seenS=new Set(); out.sectionList=[...html.matchAll(/"sectionCode":"(\d+)","sectionNumber":"([^"]+)","text":"([^"]+)"/g)].map(m=>({code:m[1],text:m[3]})).filter(x=>{if(seenS.has(x.code))return false; seenS.add(x.code); return true;}); }
  out.header=((await p.innerText('body')).replace(/\s+/g,' ').match(/Produktnummer \(PNC\):.{0,120}/)||[''])[0];
  // open first section, then click each chip in the dialog
  for(const s of out.sectionList){
    const before=views.length;
    const chip=p.locator('button:has(span:text-is("'+s.text+'"))').last();
    if(await chip.count()){ await chip.scrollIntoViewIfNeeded().catch(()=>{}); await chip.click({force:true}).catch(()=>{}); }
    for(let i=0;i<20 && views.length===before;i++) await p.waitForTimeout(500);
    await p.waitForTimeout(800);
  }
  const seen=new Set();
  for(const v of views){ if(seen.has(v.sectionCode)) continue; seen.add(v.sectionCode);
    out.sections.push({code:v.sectionCode,text:v.text,picture:v.picture,parts:(v.diagramReferences||[]).map(d=>({pos:d.posNumber,no:d.sparepart&&d.sparepart.code,name:d.sparepart&&d.sparepart.name,price:d.sparepart&&d.sparepart.price&&d.sparepart.price.value,stock:d.sparepart&&d.sparepart.stock&&d.sparepart.stock.stockLevel,url:d.sparepart&&d.sparepart.url}))}); }
 }catch(e){ out.error=e.message.split('\n')[0]; }
 console.log(JSON.stringify(out));
 await b.close();
})();
