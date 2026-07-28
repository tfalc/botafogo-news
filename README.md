# Portal Fogão

Portal de notícias do **Botafogo de Futebol e Regatas** — Jamstack com Angular no GitHub Pages, conteúdo versionado no Git e tooling Python.

**Site publicado:** [https://tfalc.github.io/botafogo-news/](https://tfalc.github.io/botafogo-news/)

Tom editorial: otimista com o Fogão; leitura crítica (sem calúnia) para rivais. Ver [`content/EDITORIAL.md`](content/EDITORIAL.md).

Marca e escudos: ver [`docs/branding/USAGE-RIGHTS.md`](docs/branding/USAGE-RIGHTS.md). Manual oficial baixável com `pwsh docs/branding/download-brand-manual.ps1` (referência local; PDF gitignored).

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | Angular 20 (standalone + signals) |
| Conteúdo | Markdown/JSON em `content/` |
| CRM | Hub em `/admin` (Decap para conteúdo + tela de tabelas) |
| Tooling | Python (Pydantic, RSS, objetivos) |
| Deploy | GitHub Actions → GitHub Pages (`main` protegida) |

## Fluxo de publicação (branch → PR → main)

A branch de produção é **`main`** (papel de “master”). Não envie commits direto nela.

1. Crie uma branch (`feature/…`, `content/…`, `fix/…`, `chore/…`).
2. Faça commit e `git push -u origin HEAD`.
3. O workflow **Abrir PR para main** cria o pull request automaticamente.
4. Aguarde o CI (`validate-and-build`) ficar verde, revise o diff e faça **Merge** (em repo solo não há autoaprovação do autor).
5. Após o merge em `main`, o workflow **Deploy Portal Fogão** publica no Pages.

Guia de proteção: [`.github/BRANCH-PROTECTION.md`](.github/BRANCH-PROTECTION.md).

Site após o deploy: [https://tfalc.github.io/botafogo-news/](https://tfalc.github.io/botafogo-news/).

## Atualizar o site (estilo FTP)

1. Edite arquivos em `content/` **ou** use o CRM em `/admin/` (após configurar OAuth em produção).
2. Commit na sua branch e push (o Actions abre o PR para `main`).
3. Após o CI verde e o merge em `main`, o workflow publica o Angular no Pages.

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

### Atualizar tabelas (competições ativas)

Abra **`/admin/tabelas.html`**. A lista de competições vem de `site.json → activeCompetitions`.

| Fonte | Chave? | Nota |
|-------|--------|------|
| **Sofascore** (padrão) | Não | API com TLS Chrome (`curl_cffi`); tabela ou chave mata-mata |
| **Google** | `SERPAPI_KEY` opcional | Google Sports via SerpAPI; sem chave usa Wikipedia (resultado típico no Google BR) |
| **ESPN** | Não | Endpoint público |
| **API-Football** | `API_FOOTBALL_KEY` | Plano free |
| **football-data.org** | `FOOTBALL_DATA_TOKEN` | BSA pode ser pago |

CLI: `npm run update:standings -- --competition all-active --provider sofascore`

Config: [`content/config/standings_sources.json`](content/config/standings_sources.json).
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

**URL pública:** [https://tfalc.github.io/botafogo-news/](https://tfalc.github.io/botafogo-news/)

1. Settings → Pages → Source: **GitHub Actions**
2. Merge em `main` (via PR com CI verde) dispara o deploy
3. Repositório: [tfalc/botafogo-news](https://github.com/tfalc/botafogo-news) — o workflow usa `github.event.repository.name` no `--base-href`

Para rotas profundas no SPA, o workflow publica o `browser` output e copia `index.html` → `404.html` (GitHub Pages serve `404.html` em paths desconhecidos).
## Roadmap

- Simulador de próximas partidas
- FastAPI CRM (aprovação, auditoria)
- Ingestão automática de tabelas
- PWA / elenco
