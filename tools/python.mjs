import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

/** Prefer project .venv; fall back to system Python (CI edge cases). */
export function resolvePython() {
  const win = process.platform === 'win32';
  const venvPy = win
    ? join(root, '.venv', 'Scripts', 'python.exe')
    : join(root, '.venv', 'bin', 'python');
  if (existsSync(venvPy)) {
    return venvPy;
  }
  return win ? 'python' : 'python3';
}

export function runPython(args, { cwd = root, stdio = 'inherit' } = {}) {
  const py = resolvePython();
  return spawnSync(py, args, { cwd, stdio });
}
