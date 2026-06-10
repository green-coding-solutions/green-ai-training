const { firefox } = require('playwright');

(async () => {
  const url = process.argv[2] || 'http://localhost:8080/js-animation.html';
  const browser = await firefox.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(55000);
  const count = await page.evaluate(() => window.frameCount);
  const ts = String(BigInt(Date.now()) * 1000000n).slice(0, 16);
  console.log(`${ts} animation_frames=${count}`);
  await browser.close();
})();
