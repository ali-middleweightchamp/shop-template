const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({viewport:{width:1280,height:820}});
  await p.goto('http://127.0.0.1:8000/catalog/',{waitUntil:'networkidle'});
  await p.evaluate(pr => document.documentElement.dataset.preset = pr, process.env.PRESET);
  await p.waitForTimeout(500);
  await p.screenshot({path:process.env.OUT});
  await b.close();
})();
