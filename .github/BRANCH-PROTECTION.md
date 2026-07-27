# Proteção de `main` (modo solo)

O repositório usa **`main`** como branch de produção. Deploy no Pages só ocorre após merge em `main`.

## Por que não “aprovar o próprio PR”?

No GitHub, **o autor de um PR não pode aprová-lo**. Em repo com um único mantenedor, exigir 1+ reviews trava o fluxo.

Solução usada aqui:

1. Você abre a branch e o Actions cria o PR
2. Espera o CI (`validate-and-build`) ficar **verde**
3. Você mesmo revisa o diff e clica em **Merge** (não em Approve)

Não é preciso (nem possível) se autoaprovar.

## Proteção ativa em `main`

- Status check obrigatório: `validate-and-build`
- Force push / delete de `main` bloqueados
- **Sem** required approving reviews (modo solo)

Ajuste em **Settings → Branches → Branch protection rules**.

## Fluxo do dia a dia

```text
feature/minha-mudanca  ──push──►  Actions abre PR → main
                                      │
                                      ▼
                               CI verde (validate-and-build)
                                      │
                                      ▼
                         você revisa o diff e faz Merge
                                      │
                                      ▼
                          Deploy Pages (workflow Deploy)
```

## Se no futuro houver outro revisor

Em Settings → Branches, ative **Require a pull request before merging** com **Required approvals: 1** (e opcionalmente Code Owners).
