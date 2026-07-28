# Branding — direitos de uso (Portal Fogão)

Documento de validação para o projeto. **Não é parecer jurídico formal**; se o site passar a ter anúncios, doações, loja ou parecer “oficial”, reavalie com advogado e/ou o programa de licenciamento do clube.

## Contexto deste projeto

- **Natureza:** portal **informativo / editorial** (notícias, tabelas, objetivos).
- **Monetização (hoje):** sem patrocínio, anúncios ou doação.
- **Decisão vigente:** **nada de escudos** (Botafogo ou outros) no site público por enquanto — usar nome em texto e, se necessário, badges de iniciais originais.

Ser “não comercial” **reduz o risco prático** (clubes priorizam quem vende ou se passa por oficial), mas **não equivale a licença automática** para usar distintivos registrados. Nomes em texto em contexto noticioso seguem ok; o escudo como identidade visual do site continua sendo o ponto sensível.

## Fontes consultadas

| Fonte | URL | Uso nesta pesquisa |
|-------|-----|--------------------|
| Manual da Marca (PDF oficial, ~93 págs.) | https://static.botafogo.com.br/upload/manual_marca.pdf | Baixado localmente como referência visual |
| Página Manual (Social & Olímpico) | https://botafogofrsocialolimpico.com.br/manualdamarca/ | Confirma oferta de download do manual |
| Licenciamento Botafogo | https://botafogo.com.br/licenciamento | Uso comercial / produtos exige licença |
| Símbolos (história do escudo) | https://www.botafogo.com.br/simbolos | Contexto histórico; não libera uso |
| Tipografias BFR Manga / Dalva | https://www.botafogo.com.br/noticias/manga-e-dalva-a-nova-voz-do-fogao | Fontes **proprietárias** do clube |
| Cobertura jornalística da divulgação do manual | — | Contexto público (abr/2024) da reformulação do site oficial |
| Lei 9.279/1996 (marcas) | legislação federal | Proteção de marca registrada |
| Lei 9.615/1998 art. 87 (Pelé) | legislação desportiva | Símbolos de entidades esportivas |
| Casos de enforcement | ConJur, Estadão, Terra, etc. | Clubes notificam uso sem licença |
| Wikimedia (logo Botafogo) | Wikipedia/Commons file page | Aviso explícito de **trademark** |

---

## Botafogo — o que pode / não pode no portal

### Seguro para o projeto (sem licença específica)

- **Nome do clube em texto** em contexto editorial/noticioso (“Botafogo”, “Fogão”, “Glorioso”), como qualquer veículo de imprensa menciona o time.
- **Cores genéricas preto e branco** na UI (não são exclusivas por si só).
- **Identidade própria do “Portal Fogão”**: tipografias de livre uso (ex.: Google Fonts), layout, textos, selos editoriais criados por nós.
- **Manual da Marca em `docs/branding/`** apenas como **referência interna de design** (o clube publicou o PDF para download). Isso **não** autoriza copiar escudo, monogramas oficiais ou tipografia BFR no site público.

### Exige licença / autorização (não usar no app sem acordo)

- **Escudo oficial** (estrela solitária no escudo suíço) como logo do site, favicon, splash, og:image, etc.
- **Arquivos oficiais de marca** (SVG/PNG do distintivo) embutidos no front.
- **Tipografias BFR Manga e BFR Dalva** (proprietárias; parceria Naipe Foundry / SAF).
- Qualquer material que sugira **site oficial**, **loja oficial** ou **produto licenciado**.
- Merchandising, camisas, stickers, apps pagos com o escudo.

O clube mantém programa de [licenciamento](https://botafogo.com.br/licenciamento) e combate à pirataria. O escudo está registrado no INPI (há décadas; ver também cobertura sobre conflitos de marca com homônimos).

### Zona cinzenta (avaliar com cautela)

- **Favicon / marca d’água** “inspirados” demais no escudo → risco de confusão de marca.
- **Monetização** (AdSense, afiliados, loja) em site que usa visual muito próximo do oficial → aumenta risco de notificação.
- Uso editorial de **foto oficial** de jogo/elenco: além de marca, há direitos de imagem (CBF, clubes, fotógrafos). Preferir conteúdo próprio ou com licença clara.

**Decisão do projeto:** não publicar o escudo oficial no Angular. Usar wordmark textual + preto/branco + tipografia livre.

---

## Escudos dos outros times (tabelas)

### Conclusão

**Não usar escudos oficiais** (Flamengo, Palmeiras, Fluminense, Vasco, etc.) nas tabelas **sem licença de cada clube** (e, em competições, atenção a ativos da CBF/CONMEBOL).

Motivos:

1. Marcas e símbolos esportivos são protegidos (LPI + Lei Pelé art. 87).
2. Há jurisprudência e notificações frequentes por uso comercial/não autorizado de escudos ([exemplo STJ/ConJur](https://www.conjur.com.br/2017-ago-16/empresa-condenada-reproduzir-escudos-times-autorizacao/), coberturas recentes sobre fanpages e artesãos).
3. Arquivos no Wikimedia Commons **não** liberam trademark: páginas de logos costumam ter aviso *Trademarked*.

### Alternativa segura para o portal

| Abordagem | Status |
|-----------|--------|
| Nome do time em texto | OK |
| Abreviação (BOT, FLA, PAL) em badge geométrico **original** | OK (criar nós) |
| Círculo monocromático com iniciais | OK |
| Escudo SVG/PNG oficial ou “quase idêntico” | **Não** |
| Pacotes de “football crests” de marketplaces sem prova de licença | **Não** |

API de dados (API-Football etc.) às vezes serve URLs de logos: o fato de a API hospedar **não** transfere direito de redistribuir no seu domínio.

---

## Matriz rápida

| Ativo | No repositório `docs/` (referência) | No site público (`apps/web`) |
|-------|--------------------------------------|------------------------------|
| Manual da Marca PDF | Sim (referência) | Não embutir |
| Escudo Botafogo | Não baixar para uso em produção | Não |
| Escudos rivais | Não | Não |
| Cores P&B + UI própria | — | Sim |
| Fontes BFR Manga/Dalva | Não | Não (usar fontes livres) |
| Nome “Botafogo” em notícias | — | Sim (editorial) |

---

## Próximos passos recomendados

1. Manter UI atual (wordmark + P&B) alinhada ao espírito do manual **sem copiar** o distintivo.
2. Nas tabelas, evoluir para **badges de iniciais** (componente próprio), nunca escudos.
3. Se quiser logo oficial no ar: abrir contato em [botafogo.com.br/licenciamento](https://botafogo.com.br/licenciamento).
4. Não versionar o PDF grande no Git (ver `.gitignore`); baixar de novo com o script em `docs/branding/`.
