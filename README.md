# Portal Fogão

Portal de notícias do **Botafogo de Futebol e Regatas** — Jamstack com Angular no GitHub Pages, conteúdo versionado no Git e tooling Python.

Tom editorial: otimista com o Fogão; leitura crítica (sem calúnia) para rivais. Ver [`content/EDITORIAL.md`](content/EDITORIAL.md).

Marca e escudos: ver [`docs/branding/USAGE-RIGHTS.md`](docs/branding/USAGE-RIGHTS.md). Manual oficial baixável com `pwsh docs/branding/download-brand-manual.ps1` (referência local; PDF gitignored).

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | Angular 20 (standalone + signals) |
| Conteúdo | Markdown/JSON em `content/` |
| CRM | Hub em `/admin` (Decap para conteúdo + tela de tabelas) |
| Tooling | Python (Pydantic, RSS, objetivos) |
| Deploy | GitHub Actions → GitHub Pages |

## Atualizar o site (estilo FTP)

1. Edite arquivos em `content/` **ou** use o CRM em `/admin/` (após configurar OAuth em produção).
2. Commit e push para `main`.
3. O workflow valida conteúdo, calcula objetivos, gera JSON e publica o Angular.

Localmente:

```bash
# Python (venv 3.12+)
npm run setup:python
# Se o venv antigo for < 3.12:
npm run setup:python:recreate
# Windows: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate

npm run validate
npm run objectives
npm run curate                  # gera drafts a partir do RSS

# Portal + CRM
npm install                     # raiz: decap-server + concurrently
cd apps/web && npm install && cd ../..
npm run dev
```

- Portal: http://localhost:4200/
- **CRM (hub):** http://localhost:4200/admin/
- **Editor Decap:** http://localhost:4200/admin/conteudo.html
- **Atualizar tabelas:** http://localhost:4200/admin/tabelas.html
- Proxy do CMS: porta 8081 (`decap-server`) · tools: porta 8090

No hub você escolhe a tarefa. Em **Conteúdo** cria/edita/apaga notícias, site, jogos e tabelas. O watcher regenera o JSON do site após salvar.

### Atualizar tabela do Brasileirão

Abra **`/admin/tabelas.html`** (não fica em Site nem no JSON da tabela). Escolha a fonte e atualize:

| Fonte | Chave? | Nota |
|-------|--------|------|
| **ESPN** (padrão) | Não | Endpoint público; bom para editorial. Confira com a CBF se quiser. |
| **API-Football** | `API_FOOTBALL_KEY` no `.env` | Plano free em [api-football.com](https://www.api-football.com/) |
| **football-data.org** | `FOOTBALL_DATA_TOKEN` | BSA pode exigir plano pago |

Também via CLI: `npm run update:standings` (usa ESPN por padrão).

Configuração das fontes: [`content/config/standings_sources.json`](content/config/standings_sources.json).

Só o portal: `npm start` · Só o CMS proxy: `npm run cms`

Build de produção:

```bash
cd apps/web
npm run build -- --base-href=/botafogo-news/
```

## Estrutura

```
apps/web/          Angular (portal)
content/           Fonte da verdade (notícias, tabelas, fixtures, objetivos)
admin/             CRM (hub, Decap, tabelas)
tools/             Scripts Python + prepare-web.mjs
.github/workflows  Deploy Pages
```

## Notícias

- `status: draft` — não aparece no site
- `status: validated` — publicada
- `tone: fogao | rival` — guia o selo editorial

Curadoria RSS: `python tools/curate_rss.py` cria rascunhos; revise e valide antes de publicar.

## Objetivos (FogaoNET)

`python tools/compute_objectives.py` gera `content/objectives/snapshot.json` com gaps para:

- Título
- Libertadores (G6)
- Sul-Americana
- Evitar Z4

Limiares configuráveis em `content/objectives/config.json`.

## Decap CMS no GitHub Pages

O CRM estático fica em `/admin` (hub + `conteudo.html` + `tabelas.html`). Para autenticação do editor:

1. Opção A (recomendada com Pages puro): `admin/config.yml` já usa `backend.name: github` — configure [Decap GitHub OAuth](https://decapcms.org/docs/github-backend/) (ou [netlify-cms-oauth](https://github.com/vencax/netlify-cms-github-oauth-provider)).
2. Opção B: hospede só o CMS auth no Netlify Identity + Git Gateway (site ainda pode ser Pages).
3. Desenvolvimento local: `local_backend: true` + `npm run dev` (decap-server na 8081).
## GitHub Pages

1. Settings → Pages → Source: **GitHub Actions**
2. Push em `main`
3. Repositório: [tfalc/botafogo-news](https://github.com/tfalc/botafogo-news) — o workflow já usa `github.event.repository.name` no `--base-href`
4. Após o primeiro deploy: Settings → Pages → Source: **GitHub Actions**. Site em `https://tfalc.github.io/botafogo-news/`

Para rotas profundas no SPA, o workflow publica o `browser` output; se necessário, copie `index.html` para `404.html` no artifact (GitHub Pages serve 404.html em paths desconhecidos).

## Roadmap

- Simulador de próximas partidas
- FastAPI CRM (aprovação, auditoria)
- Ingestão automática de tabelas
- PWA / elenco
