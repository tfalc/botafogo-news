# Atualização de tabelas

Fontes e aliases: [`standings_sources.json`](standings_sources.json).

Providers principais:

- **sofascore** — API (TLS Chrome / `curl_cffi`); tabela ou chave (mata-mata)
- **google** — SerpAPI (`SERPAPI_KEY`) ou scrape Wikipedia (resultado típico no Google BR)
- espn / api-football / football-data — opções extras

Competições ativas vêm de `content/site.json` → `activeCompetitions`. O CRM lista só essas.

```bash
npm run update:standings -- --competition brasileirao --provider sofascore
npm run update:standings -- --competition all-active --provider google
```
