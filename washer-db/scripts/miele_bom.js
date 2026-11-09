// Read-only: Miele spare-parts catalogue (MSD), anonymous access, no cart. Usage: node miele_bom.js CODE[:PREF] ...
const { chromium } = require('playwright'); const fs=require('fs');
(async () => {
  const args=process.argv.slice(2);
  const b = await chromium.launch(); const p = await (await b.newContext({locale:'nb-NO'})).newPage();
  await p.goto('https://www4.miele.de/msd?vg=VG-NO&country=NO&language=no', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await p.waitForTimeout(6000);
  const get = async (path) => p.evaluate(async(path)=>{ const r=await fetch(path); return {s:r.status, t:await r.text()}; }, path);
  for (const a of args) {
    const [code,pref]=a.split(':'); const f=`raw/miele/${code}.json`;
    if (fs.existsSync(f)) continue;
    const out={code,checked:new Date().toISOString()};
    try {
      const s=await get('/msd/api/devicetypesearch/device-type-search?text='+code); const devs=JSON.parse(s.t||'[]').filter(d=>d.articleGroupId===2||/wash/i.test(d.guiIdArtGrp||'')||true);
      out.devices=devs.map(d=>({id:d.id,modelName:d.modelName,typbez:d.typbez,objschlETD:d.objschlETD,start:d.startDate,end:d.endDate,group:d.guiIdArtGrp}));
      let dev=devs.filter(d=>(d.typbez||'').toUpperCase()===code.toUpperCase());
      const p2=(pref||'WCS').toUpperCase(); const dp=dev.filter(d=>d.modelName.toUpperCase().replace(/\s/g,'').includes(p2)); if(dp.length) dev=dp;
      dev.sort((x,y)=>(y.startDate||'').slice(3).localeCompare((x.startDate||'').slice(3)));
      if(!dev.length){ out.error='no device'; fs.writeFileSync(f,JSON.stringify(out)); console.error(code,'no device'); continue; }
      const d=dev[0]; out.device={id:d.id,modelName:d.modelName,objschlETD:d.objschlETD}; out.url=`https://www4.miele.de/msd?vg=VG-NO&country=NO&language=no#/device/${d.id}/dashboard`;
      let ov=null; for(let k=0;k<4;k++){ const rr=await get('/msd/api/etd/functiongroup/overview?msdId='+d.id); try{ ov=JSON.parse(rr.t); }catch(e){ ov=null; } if(Array.isArray(ov)) break; out.retry=(out.retry||0)+1; await p.waitForTimeout(30000); } if(!Array.isArray(ov)) throw new Error('overview not available (throttled?)');
      out.groups=[];
      for (const g of ov) {
        await p.waitForTimeout(1500);
        const det=await get(`/msd/api/etd/functiongroup/details?objKeyModel=${d.objschlETD}&objKeyFgr=${g.fgrObjectKey}&isVatIncluded=true&lang=no`);
        let pos=[]; if(det.s!==200){ await p.waitForTimeout(20000); } try{ pos=(JSON.parse(det.t).completeData.positionList||[]).map(x=>({fig:x.fig,pos:x.kiPos,no:x.objMaterial.materialNumber,name:x.objMaterial.designation,price:x.objMaterial.materialMasterData.price,qty:x.qty,type:x.posType})); }catch(e){}
        out.groups.push({num:g.numberId,desc:g.description,key:g.fgrObjectKey,parts:pos});
      }
    } catch(e){ out.error=e.message.slice(0,200); }
    fs.writeFileSync(f,JSON.stringify(out)); console.error(code, out.device&&out.device.modelName, (out.groups||[]).length, out.error||'');
  }
  await b.close();
})();
