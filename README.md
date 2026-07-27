# Portal Fogão

Portal de notícias do **Botafogo de Futebol e Regatas** — Jamstack com Angular no GitHub Pages, conteúdo versionado no Git e tooling Python.

Tom editorial: copo sempre meio cheio para o Fogão; leitura crítica (sem calúnia) para rivais. Ver [`content/EDITORIAL.md`](content/EDITORIAL.md).

## Stack

| Camada | Tecnologia |
|--------|------------|
| Frontend | Angular 20 (standalone + signals) |
| Conteúdo | Markdown/JSON em `content/` |
| CMS | Decap CMS em `/admin` (git-based) |
| Tooling | Python (Pydantic, RSS, objetivos) |
| Deploy | GitHub Actions → GitHub Pages |

## Atualizar o site (estilo FTP)

1. Edite arquivos em `content/` **ou** use o Decap em `/admin` (após configurar OAuth).
2. Commit e push para `main`.
3. O workflow valida conteúdo, calcula objetivos, gera JSON e publica o Angular.

Localmente:

```bash
# Python
pip install -r tools/requirements.txt
python tools/validate_content.py
python tools/compute_objectives.py
python tools/curate_rss.py          # gera drafts a partir do RSS

# Angular
cd apps/web
npm install
npm start                           # roda prepare-web + ng serve
```

Build de produção:

```bash
cd apps/web
npm run build -- --base-href=/botafogo-news/
```

## Estrutura

```
apps/web/          Angular (portal)
content/           Fonte da verdade (notícias, tabelas, fixtures, objetivos)
admin/             Decap CMS (config + index)
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

O admin estático fica em `/admin`. Para autenticação:

1. Opção A (recomendada com Pages puro): altere `admin/config.yml` para `backend.name: github` e configure [Decap Git Gateway / GitHub OAuth App](https://decapcms.org/docs/github-backend/) (ou use [netlify-cms-oauth](https://github.com/vencax/netlify-cms-github-oauth-provider) em free tier).
2. Opção B: hospede só o CMS auth no Netlify Identity + Git Gateway (site ainda pode ser Pages).
3. Desenvolvimento local: descomente `local_backend: true` e rode `npx decap-server`.

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
