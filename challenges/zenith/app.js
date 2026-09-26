'use strict';

const KoaRequest = require('koa/lib/request');
Object.defineProperty(KoaRequest, 'hostname', {
  get() {
    const host = this.get('host');
    if (!host) return '';
    if ('[' === host[0]) return this.URL.hostname;
    return host.split(':', 1)[0];
  },
  configurable: true,
});

const Koa = require('koa');
const Router = require('@koa/router');
const bodyParser = require('koa-bodyparser');
const serve = require('koa-static');
const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const app = new Koa();
const router = new Router();

const FLAG2 = process.env.FLAG2;

try {
  fs.writeFileSync('/home/ctfuser/flag.txt', FLAG2 + '\n', { mode: 0o600 });
} catch (_) { /* expected outside container */ }

router.get('/', async (ctx) => {
  ctx.type = 'html';
  ctx.body = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>[Zulu] EverSec DevTools</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Courier New', monospace; background: #0d1117; color: #c9d1d9; padding: 40px; min-height: 100vh; }
    h1 { color: #58a6ff; border-bottom: 1px solid #30363d; padding-bottom: 12px; margin-bottom: 24px; font-size: 1.6rem; }
    .badge { display: inline-block; background: #1f3a5f; color: #58a6ff; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 12px; }
    .card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 20px; margin-bottom: 20px; }
    .card p { color: #8b949e; margin-bottom: 10px; line-height: 1.6; }
    .card ul { color: #8b949e; padding-left: 20px; line-height: 1.8; }
    .card ul li span { color: #c9d1d9; }
    .status { display: flex; align-items: center; gap: 8px; }
    .dot { width: 8px; height: 8px; background: #3fb950; border-radius: 50%; }
    a { color: #58a6ff; text-decoration: none; }
    a:hover { text-decoration: underline; }
    .footer { margin-top: 32px; color: #484f58; font-size: 0.85rem; }
  </style>
</head>
<body>
  <h1>&#x1F6E0;&#xFE0F; EverSec Developer Tools Portal</h1>
  <div class="card">
    <div class="badge">Internal Use Only</div>
    <p>Authorized personnel only. This portal provides internal developer utilities for the EverSec platform.</p>
    <ul>
      <li><span>Admin scripting platform</span> &mdash; localhost access only</li>
      <li><span>Deployment configuration management</span></li>
      <li><span>Service health monitoring</span></li>
    </ul>
  </div>
  <div class="card">
    <div class="status"><div class="dot"></div><span>Operational</span></div>
    <p style="margin-top:10px;">Version v1.4.2 &nbsp;&middot;&nbsp; Contact: <a href="mailto:dev@eversec.io">dev@eversec.io</a></p>
  </div>
  <div class="footer">EverSec Security Solutions &copy; 2026</div>
</body>
</html>`;
});

// Admin scripting platform — localhost only.
router.post('/admin/execute', async (ctx) => {
  const rawHost = ctx.get('host') || '';

  const BLOCKED = ['localhost', '127.0.0.1', '::1', '0.0.0.0', '[::1]'];
  if (!rawHost.includes('@') && BLOCKED.includes(rawHost.split(':')[0].toLowerCase())) {
    ctx.status = 403;
    ctx.body = { error: 'Admin scripting platform is only accessible from localhost' };
    return;
  }

  if (ctx.hostname !== 'localhost' && ctx.hostname !== '127.0.0.1') {
    ctx.status = 403;
    ctx.body = { error: 'Admin scripting platform is only accessible from localhost' };
    return;
  }

  const { script } = ctx.request.body;
  if (!script || typeof script !== 'string') {
    ctx.status = 400;
    ctx.body = { error: 'Missing required parameter: script' };
    return;
  }

  try {
    const output = execSync(script, {
      shell: '/bin/sh',
      encoding: 'utf8',
      timeout: 5000,
      cwd: '/tmp',
    });
    ctx.body = { success: true, output };
  } catch (err) {
    ctx.body = { success: false, output: err.stdout || '', error: err.message };
  }
});

app
  .use(bodyParser())
  .use(router.routes())
  .use(router.allowedMethods())
  .use(serve(path.join(__dirname), { hidden: true }));

const PORT = 4022;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`[*] EverSec DevTools running on port ${PORT}`);
});
