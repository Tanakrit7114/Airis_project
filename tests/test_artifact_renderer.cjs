// Requires @playwright/test on NODE_PATH and an installed Chrome channel.
// This isolates the real artifact component; no chat/API calls or saved history.
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { createServer } = require('node:http');
const esbuild = require('../web/node_modules/esbuild');
const { chromium, expect } = require('@playwright/test');

(async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'airis-artifacts-'));
  let browser;
  let networkAttempts = 0;
  const html = `<!doctype html><html lang="th"><head><meta http-equiv="refresh" content="0;url=/unexpected"></head><body><h1>เว็บไซต์ทดสอบ</h1><button id="counter" onclick="this.textContent='Clicked'">Click</button><output id="isolation"></output><script>try { parent.document.body; document.querySelector('#isolation').textContent='unsafe'; } catch { document.querySelector('#isolation').textContent='isolated'; } fetch('/unexpected').catch(()=>{});</script></body></html>`;
  const python = 'print("สวัสดี")';
  const markdown = '```html\n' + html + '\n```\n\n```python\n' + python + '\n```';
  const built = await esbuild.build({
    stdin: {
      contents: `import React from 'react'; import {createRoot} from 'react-dom/client'; import MarkdownContent from './src/components/MarkdownContent'; createRoot(document.getElementById('root')).render(React.createElement(MarkdownContent,{content:window.fixture}));`,
      resolveDir: path.join(__dirname, '../web'), loader: 'jsx',
    },
    bundle: true, write: false, format: 'iife', loader: { '.css': 'empty' },
  });
  const fixture = JSON.stringify(markdown).replace(/</g, '\\u003c');
  const server = createServer((req, res) => {
    if (req.url === '/bundle.js') {
      res.writeHead(200, { 'Content-Type': 'text/javascript' });
      res.end(built.outputFiles[0].text);
    } else if (req.url === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end(`<html><body><div id="root"></div><script>window.fixture=${fixture};</script><script src="/bundle.js"></script></body></html>`);
    } else {
      if (req.url === '/unexpected') networkAttempts++;
      res.writeHead(404); res.end();
    }
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try {
    browser = await chromium.launch({ channel: 'chrome', headless: true });
    const context = await browser.newContext({ acceptDownloads: true, permissions: ['clipboard-read', 'clipboard-write'] });
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`http://127.0.0.1:${server.address().port}/`);
    await expect(page.getByRole('button', { name: 'Download HTML', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Copy code', exact: true }).last().click();
    await expect(page.getByRole('status').last()).toHaveText('Copied');
    assert.equal(await page.evaluate(() => navigator.clipboard.readText()), python);
    for (const [name, filename, expected] of [['Download HTML', 'airis-website.html', html], ['Download code', 'airis-code.py', python]]) {
      const pending = page.waitForEvent('download');
      await page.getByRole('button', { name, exact: true }).click();
      const download = await pending;
      assert.equal(download.suggestedFilename(), filename);
      const destination = path.join(directory, filename);
      await download.saveAs(destination);
      assert.equal(await fs.readFile(destination, 'utf8'), expected);
    }
    await page.getByRole('button', { name: 'Open / refresh preview' }).click();
    await expect(page.locator('iframe')).toHaveAttribute('sandbox', 'allow-scripts');
    const frame = page.frameLocator('iframe');
    await expect(frame.getByRole('heading', { name: 'เว็บไซต์ทดสอบ' })).toBeVisible();
    await expect(frame.locator('#isolation')).toHaveText('isolated');
    await frame.getByRole('button', { name: 'Click', exact: true }).click();
    await expect(frame.getByRole('button', { name: 'Clicked', exact: true })).toBeVisible();
    assert.equal(networkAttempts, 0);
    await page.getByRole('button', { name: 'Close preview', exact: true }).click();
    await expect(page.locator('iframe')).toHaveCount(0);
    assert.deepEqual(errors, []);
    console.log('Artifact browser checks passed: clipboard, exact HTML/Python downloads, interactive preview, isolated parent, blocked fetch/refresh, close.');
  } finally {
    await browser?.close();
    server.closeAllConnections();
    await new Promise(resolve => server.close(resolve));
    await fs.rm(directory, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
