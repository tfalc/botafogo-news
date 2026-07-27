# Proteção de `main` (aprovação obrigatória)

O repositório usa **`main`** como branch de produção (equivalente ao “master” do fluxo clássico). Deploy no Pages só ocorre após merge em `main`.

## Ativar no GitHub (uma vez)

1. Abra **Settings → Rules → Rulesets → New branch ruleset** (ou *Branches → Add branch protection rule*).
2. Target: `main`.
3. Marque:
   - **Restrict deletions**
   - **Require a pull request before merging**
   - **Require approvals:** `1` (com segundo revisor; em conta solo o dono ainda pode fazer merge se *Do not allow bypassing* estiver off)
   - **Require review from Code Owners** (opcional — usa [`.github/CODEOWNERS`](CODEOWNERS))
   - **Require status checks to pass:** `validate-and-build`
   - **Block force pushes**
4. Salve o ruleset.

Já foi aplicada proteção clássica em `main` via API (PR + CI; force push bloqueado). Para modo estrito com segundo revisor, ative *Include administrators* / *Do not allow bypassing* nas Settings.

## Fluxo do dia a dia

```text
feature/minha-mudanca  ──push──►  Actions abre PR → main
                                      │
                                      ▼
                               revisão + approve
                                      │
                                      ▼
                                    merge
                                      │
                                      ▼
                          Deploy Pages (workflow Deploy)
```

Nomes sugeridos de branch: `feature/…`, `fix/…`, `content/…`, `chore/…`.

O workflow [`.github/workflows/open-pr.yml`](workflows/open-pr.yml) cria o PR automaticamente em todo push fora de `main`.
