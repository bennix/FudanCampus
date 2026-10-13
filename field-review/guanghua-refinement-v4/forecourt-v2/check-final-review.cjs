const {chromium} = require('C:/Users/Lumin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const errors = [], failedResponses = [];
  const browser = await chromium.launch({
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
    headless: true,
    args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  try {
    const page = await browser.newPage({viewport: {width: 1400, height: 1000}});
    page.on('pageerror', e => errors.push(e.message));
    page.on('response', response => {
      if (response.status() >= 400) failedResponses.push({url: response.url(), status: response.status()});
    });
    await page.goto('http://127.0.0.1:8771/field-review/guanghua-refinement-v4/forecourt-v2/review.html');
    await page.waitForFunction(() => window.__ready || window.__error, null, {timeout: 180000});
    const state = await page.evaluate(() => ({ready: window.__ready, error: window.__error,
      meshCount: window.__meshCount, render: window.__renderInfo}));
    if (!state.ready) throw Error(JSON.stringify(state));
    const views = ['entry', 'top', 'plaza', 'edge', 'statue', 'plaque', 'statueBack', 'overall'];
    for (const view of views) {
      await page.locator(`[data-view="${view}"]`).click();
      await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
      if (['entry', 'statue', 'plaque'].includes(view)) {
        await page.locator('canvas').screenshot({path: path.join(__dirname, `web-final-${view}.png`)});
      }
    }
    const inscriptions = await page.evaluate(() => {
      const result = [];
      window.__scene.traverse(o => {
        if (o.name.includes('驢背詩思') || o.name.includes('inset_nameplate')) {
          result.push({name: o.name, isMesh: !!o.isMesh, featureId: o.userData.feature_id});
        }
      });
      return result;
    });
    if (!inscriptions.some(o => o.name.includes('驢背詩思') && o.isMesh && o.featureId === 'POET_DONKEY')) {
      throw Error('Exported plaque inscription absent');
    }
    await page.locator('#toggle').click();
    await page.waitForFunction(() => document.querySelector('#toggle').textContent === '显示树叶');
    await page.locator('#toggle').click();
    const images = await page.evaluate(async () => {
      await Promise.all([...document.images].map(im => im.decode().catch(() => {})));
      return [...document.images].map(im => ({src: im.getAttribute('src'), width: im.naturalWidth, height: im.naturalHeight}));
    });
    if (images.some(im => !im.width || !im.height)) throw Error('Review image failed to load');
    await page.setViewportSize({width: 390, height: 844});
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
    const result = {...state, reviewedAt: new Date().toISOString(), views: views.length,
      plaqueView: true, inscriptions, images, foliageToggle: true, mobileWidth: 390,
      overflow, errors, failedResponses};
    fs.writeFileSync(path.join(__dirname, 'final-browser-validation.json'), JSON.stringify(result, null, 2));
    if (errors.length || failedResponses.length || overflow) throw Error('Final browser review failed');
    console.log('RESUMED_FINAL_BROWSER_REVIEW_OK');
  } finally {
    await browser.close();
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
