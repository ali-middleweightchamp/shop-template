const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  for (const t of ['noir','ocean','violet','rose']) {
    const p = await b.newPage({viewport:{width:1180,height:760}});
    await p.goto('http://127.0.0.1:8000/catalog/',{waitUntil:'networkidle'});
    await p.evaluate(x=>document.documentElement.dataset.preset=x, t);
    await p.waitForTimeout(500);
    await p.screenshot({path:`/tmp/th_${t}.png`});
    await p.close();
  }
  await b.close();
})();
