import { spawnSync } from 'node:child_process';
import { cpSync, mkdirSync, existsSync, copyFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const webPublic = join(root, 'apps', 'web', 'public');

function run(cmd, args) {
  const result = spawnSync(cmd, args, { cwd: root, stdio: 'inherit' });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

const py = process.platform === 'win32' ? 'python' : 'python3';

run(py, ['tools/validate_content.py']);
run(py, ['tools/compute_objectives.py']);
run(py, ['tools/build_content.py']);

const adminOut = join(webPublic, 'admin');
mkdirSync(adminOut, { recursive: true });
cpSync(join(root, 'admin', 'index.html'), join(adminOut, 'index.html'));
cpSync(join(root, 'admin', 'config.yml'), join(adminOut, 'config.yml'));

console.log('prepare-web: content + admin ready');
