#!/usr/bin/env node
/**
 * Rebuild apps/web/public/content when content/ changes (so ng serve picks up CMS edits).
 *
 * Ignores generated objectives outputs — otherwise prepare-web writes snapshot/dashboard
 * with a new generatedAt every run and triggers an infinite rebuild/live-reload loop.
 */
import { watch } from 'node:fs';
import { spawn } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const contentDir = join(root, 'content');

let timer = null;
let running = false;
let queued = false;
/** Brief quiet window after prepare-web exits (late FS events). */
let suppressUntil = 0;

const IGNORED_SUFFIXES = [
  'objectives/snapshot.json',
  'objectives/dashboard.json',
];

function shouldIgnore(filename) {
  const normalized = String(filename).replace(/\\/g, '/').toLowerCase();
  if (normalized.endsWith('.pyc') || normalized.includes('__pycache__')) return true;
  return IGNORED_SUFFIXES.some(
    (suffix) => normalized === suffix || normalized.endsWith(`/${suffix}`),
  );
}

function rebuild() {
  if (running) {
    queued = true;
    return;
  }
  running = true;
  console.log('[content-watch] rebuild…');
  const child = spawn(process.execPath, [join(root, 'tools', 'prepare-web.mjs')], {
    cwd: root,
    stdio: 'inherit',
  });
  child.on('exit', (code) => {
    running = false;
    suppressUntil = Date.now() + 2_000;
    if (code !== 0) {
      console.error('[content-watch] prepare-web failed:', code);
    } else {
      console.log('[content-watch] ok');
    }
    if (queued) {
      queued = false;
      rebuild();
    }
  });
}

console.log(`[content-watch] observando ${contentDir}`);
console.log(
  '[content-watch] ignorando gerados: objectives/snapshot.json, objectives/dashboard.json',
);
watch(contentDir, { recursive: true }, (_event, filename) => {
  if (!filename) return;
  if (shouldIgnore(filename)) return;
  if (Date.now() < suppressUntil) return;
  clearTimeout(timer);
  timer = setTimeout(rebuild, 500);
});
