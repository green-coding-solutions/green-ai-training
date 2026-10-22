const { firefox } = require('playwright');

(async () => {
  const url = process.argv[2] || 'http://localhost:8080/css-animation.html';
  const browser = await firefox.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(55000);
  await browser.close();
})();
