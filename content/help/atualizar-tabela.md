---
title: Onde atualizar a tabela
---

# Fonte da tabela do Brasileirão

A **fonte** (ESPN, API-Football, etc.) **não** fica em Coleções → Site nem ao editar o JSON em Tabelas.

Use a tela dedicada do CRM:

1. Abra `/admin/tabelas.html`
2. Escolha a fonte (ESPN sem chave é o padrão)
3. Clique em **Atualizar classificação agora**
4. Confira em **Conteúdo → Tabelas → brasileirao** ou no site em `/tabela`

Exige `npm run dev` (serviço de tools na porta 8090).

Alternativa no terminal: `npm run update:standings`
