#!/usr/bin/env node
/**
 * Rebuild apps/web/public/content when content/ changes (so ng serve picks up CMS edits).
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
    if (code !== 0) {
      console.error('[content-watch] prepare-web failed:', code);
    } else {
      console.log('[content-watch] ok — recarregue o portal se necessário');
    }
    if (queued) {
      queued = false;
      rebuild();
    }
  });
}

console.log(`[content-watch] observando ${contentDir}`);
watch(contentDir, { recursive: true }, (_event, filename) => {
  if (!filename) return;
  const normalized = String(filename).replace(/\\/g, '/').toLowerCase();
  // Avoid feedback loop: prepare/objectives rewrite snapshot.json
  if (normalized.includes('objectives/snapshot.json')) return;
  if (normalized.endsWith('.pyc') || normalized.includes('__pycache__')) return;
  clearTimeout(timer);
  timer = setTimeout(rebuild, 500);
});
