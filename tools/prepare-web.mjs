import { cpSync, mkdirSync, existsSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { runPython } from './python.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');
const webPublic = join(root, 'apps', 'web', 'public');

if (!existsSync(join(root, '.venv')) && !process.env.CI) {
  console.error('Erro: .venv não encontrado. Rode: npm run setup:python');
  process.exit(1);
}

function runOrExit(args) {
  const result = runPython(args);
  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

runOrExit(['tools/validate_content.py']);
runOrExit(['tools/compute_objectives.py']);
runOrExit(['tools/build_content.py']);

const adminSrc = join(root, 'admin');
const adminOut = join(webPublic, 'admin');
if (existsSync(adminOut)) {
  rmSync(adminOut, { recursive: true, force: true });
}
mkdirSync(adminOut, { recursive: true });
for (const name of ['index.html', 'conteudo.html', 'tabelas.html', 'admin.css', 'config.yml']) {
  const from = join(adminSrc, name);
  if (existsSync(from)) {
    cpSync(from, join(adminOut, name));
  }
}

console.log('prepare-web: content + admin ready');
