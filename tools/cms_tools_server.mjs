#!/usr/bin/env node
/**
 * Local CRM tools API (only for npm run dev).
 * POST /update-standings  { competition?, provider? }
 * GET  /providers
 */
import http from 'node:http';
import { spawn } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { resolvePython } from './python.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const PORT = Number(process.env.CMS_TOOLS_PORT || 8090);

function loadEnv() {
  const envPath = join(root, '.env');
  if (!existsSync(envPath)) return;
  for (const line of readFileSync(envPath, 'utf8').split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith('#') || !t.includes('=')) continue;
    const i = t.indexOf('=');
    const k = t.slice(0, i).trim();
    const v = t.slice(i + 1).trim().replace(/^['"]|['"]$/g, '');
    if (!(k in process.env)) process.env[k] = v;
  }
}

function runUpdate({ competition = 'brasileirao', provider } = {}) {
  return new Promise((resolve) => {
    const py = resolvePython();
    const args = ['tools/update_standings.py', '--competition', competition];
    if (provider) args.push('--provider', provider);
    const child = spawn(py, args, {
      cwd: root,
      env: process.env,
      windowsHide: true,
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (d) => {
      stdout += d.toString();
    });
    child.stderr.on('data', (d) => {
      stderr += d.toString();
    });
    child.on('close', (code) => {
      resolve({ code: code ?? 1, stdout, stderr });
    });
  });
}

function sendJson(res, status, body) {
  const data = JSON.stringify(body);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  });
  res.end(data);
}

loadEnv();

const server = http.createServer(async (req, res) => {
  if (req.method === 'OPTIONS') {
    sendJson(res, 204, {});
    return;
  }

  const url = new URL(req.url || '/', `http://127.0.0.1:${PORT}`);

  if (req.method === 'GET' && url.pathname === '/health') {
    sendJson(res, 200, { ok: true });
    return;
  }

  if (req.method === 'GET' && url.pathname === '/providers') {
    try {
      const cfg = JSON.parse(
        readFileSync(join(root, 'content/config/standings_sources.json'), 'utf8'),
      );
      let active = Object.keys(cfg.competitions || {});
      try {
        const site = JSON.parse(readFileSync(join(root, 'content/site.json'), 'utf8'));
        if (Array.isArray(site.activeCompetitions) && site.activeCompetitions.length) {
          active = site.activeCompetitions.filter((id) => cfg.competitions?.[id]);
        }
      } catch {
        // keep keys from sources
      }
      sendJson(res, 200, { ...cfg, activeCompetitions: active });
    } catch (err) {
      sendJson(res, 500, { error: String(err) });
    }
    return;
  }

  if (req.method === 'POST' && url.pathname === '/update-standings') {
    let body = {};
    try {
      const chunks = [];
      for await (const chunk of req) chunks.push(chunk);
      if (chunks.length) body = JSON.parse(Buffer.concat(chunks).toString('utf8') || '{}');
    } catch {
      sendJson(res, 400, { error: 'JSON inválido' });
      return;
    }
    const result = await runUpdate(body);
    sendJson(res, result.code === 0 ? 200 : 500, {
      ok: result.code === 0,
      ...result,
    });
    return;
  }

  sendJson(res, 404, { error: 'not found' });
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[cms-tools] listening on http://127.0.0.1:${PORT}`);
});
