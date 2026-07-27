#!/usr/bin/env node
/** Run a Python script with the project .venv. Usage: node tools/run-python.mjs tools/foo.py [args...] */
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import { runPython } from './python.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

if (!existsSync(join(root, '.venv'))) {
  console.error('Erro: .venv não encontrado. Rode primeiro: npm run setup:python');
  process.exit(1);
}

const args = process.argv.slice(2);
if (!args.length) {
  console.error('Uso: node tools/run-python.mjs <script.py> [args...]');
  process.exit(1);
}

const result = runPython(args);
process.exit(result.status ?? 1);
