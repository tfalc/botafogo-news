#!/usr/bin/env node
/**
 * Create .venv with Python 3.12+ and install project deps.
 * Usage: node tools/setup_venv.mjs
 */
import { spawnSync } from 'node:child_process';
import { existsSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const venvDir = join(root, '.venv');
const win = process.platform === 'win32';
const recreate = process.argv.includes('--recreate');

function run(cmd, args, opts = {}) {
  const result = spawnSync(cmd, args, { cwd: root, stdio: 'inherit', ...opts });
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
  return result;
}

function runCapture(cmd, args) {
  return spawnSync(cmd, args, { cwd: root, encoding: 'utf8' });
}

/** Resolve a Python 3.12+ interpreter for creating the venv. */
function resolveBootstrapPython() {
  const candidates = win
    ? [
        ['py', ['-3.12']],
        ['py', ['-3.13']],
        ['python', []],
      ]
    : [
        ['python3.12', []],
        ['python3.13', []],
        ['python3', []],
        ['python', []],
      ];

  for (const [cmd, prefix] of candidates) {
    const check = runCapture(cmd, [...prefix, '-c', 'import sys; print(sys.version_info[:2]); raise SystemExit(0 if sys.version_info >= (3, 12) else 1)']);
    if (check.status === 0) {
      return { cmd, prefix };
    }
  }
  console.error(
    'Erro: Python 3.12+ é obrigatório (veja .python-version).\n' +
      'Instale 3.12+ e rode de novo: npm run setup:python',
  );
  process.exit(1);
}

if (recreate && existsSync(venvDir)) {
  console.log(`Removendo venv antigo: ${venvDir}`);
  rmSync(venvDir, { recursive: true, force: true });
}

const { cmd: bootstrapCmd, prefix } = resolveBootstrapPython();

if (!existsSync(venvDir)) {
  console.log(`Criando venv (Python 3.12+) em ${venvDir} ...`);
  run(bootstrapCmd, [...prefix, '-m', 'venv', '.venv']);
} else {
  console.log(`venv já existe: ${venvDir}`);
}

const pip = win
  ? join(venvDir, 'Scripts', 'pip.exe')
  : join(venvDir, 'bin', 'pip');
const py = win
  ? join(venvDir, 'Scripts', 'python.exe')
  : join(venvDir, 'bin', 'python');

const ver = runCapture(py, ['-c', 'import sys; print("{0}.{1}".format(*sys.version_info[:2])); raise SystemExit(0 if sys.version_info >= (3, 12) else 1)']);
if (ver.status !== 0) {
  console.error(
    `Erro: .venv está em Python ${ver.stdout?.trim() || '?'} (mínimo 3.12).\n` +
      'Recrie com: npm run setup:python -- --recreate',
  );
  process.exit(1);
}

run(py, ['-m', 'pip', 'install', '--upgrade', 'pip']);
run(pip, ['install', '-r', 'tools/requirements.txt']);
run(pip, ['install', '-e', '.[dev]']);

console.log(`venv pronto (Python ${ver.stdout.trim()}). Ative com:`);
if (win) {
  console.log('  .\\.venv\\Scripts\\Activate.ps1');
} else {
  console.log('  source .venv/bin/activate');
}
