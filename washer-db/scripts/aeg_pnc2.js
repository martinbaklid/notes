// Read-only: open AEG's public product page by its usual URL and read the PNC in the title/body.
const { chromium } = require('playwright');
(async () => {
  const codes=process.argv.slice(2); const out={};
  const b = await chromium.launch(); const p = await (await b.newContext({locale:'nb-NO'})).newPage();
  for (const c of codes) {
    const lc=c.toLowerCase(); const kind=lc.startsWith('lw')?'washer-dryers/free-standing-washer-dryer':'washing-machines/front-loader-washing-machine';
    out[c]={};
    for (const host of ['https://www.aeg.no','https://www.aeg.se']) {
      const url=`${host}/laundry/laundry/${kind}/${lc}/`;
      try { const r=await p.goto(url,{waitUntil:'domcontentloaded',timeout:45000}); await p.waitForTimeout(2500);
        const title=await p.title(); const t=await p.innerText('body').catch(()=> '');
        const m=(title+' '+t).match(/\b(91\d{7})\b/);
        if (r && r.status()===200 && m) { out[c]={url,title,pnc:m[1]}; break; } else out[c][host]=(r&&r.status())+' '+title.slice(0,60);
      } catch(e){ out[c][host]='ERR '+e.message.slice(0,60); }
    }
    console.error(c, JSON.stringify(out[c]));
  }
  console.log(JSON.stringify(out)); await b.close();
})();
