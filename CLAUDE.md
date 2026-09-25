# CLAUDE.md — economistarenato.com.br

> Contexto do projeto para o Claude Code. Fica na raiz do repositório e é lido
> automaticamente ao iniciar.

---

## 1. O que é este projeto

**Publicação editorial** de **Renato Wanderley Gomes** — economista (CORECON-MS nº 1297),
sócio-fundador da WGSA, pré-candidato ao Governo de Mato Grosso do Sul pela Democracia
Cristã (DC).

Desde 24/09/2026 o site deixou de ser landing page institucional e passou a funcionar como
jornal: opinião, análise e **dados abertos** sobre a economia e as contas públicas de MS e
de Campo Grande. O registro é o de **economista institucional** — toda afirmação numérica
com fonte primária verificável, e a fonte sempre visível para o leitor.

**Domínio:** `economistarenato.com.br` · **Handle:** `@economistarenato`
**Estratégia:** `projeto_mapeamento_candGov/comunicacao_digital/PLANO_AUTORIDADE_2027_2028.md`

---

## 2. Stack

- **Site estático** — HTML/CSS/JS puro, sem framework e sem build step.
- **Netlify**, deploy contínuo do GitHub `renatogomes-afk/economistarenato` (branch `main`,
  publish dir `site`). Publicar = `git add . && git commit && git push` → ~1 min.
- **Sem CMS, sem servidor, sem banco.**

---

## 3. Estrutura

```
economistarenato/
├── site/                          # ← PUBLISH DIR do Netlify
│   ├── index.html                 # capa em grade de jornal
│   ├── artigo/<slug>/index.html   # uma pasta por matéria
│   ├── sobre/index.html           # bio, método de apuração, pré-candidatura
│   ├── obrigado/index.html        # retorno do formulário (Netlify Forms)
│   ├── dados/                     # BASES ABERTAS (ver seção 5)
│   │   ├── index.html             # catálogo
│   │   ├── <slug>/index.html      # página por base (gerada)
│   │   ├── <slug>.json / .csv     # arquivos da base (gerados)
│   │   ├── fontes/*.pdf           # documentos primários espelhados
│   │   └── indicadores.json       # painel "MS em números" da capa
│   ├── assets/estilo.css          # sistema visual inteiro
│   ├── assets/tabela.js           # tabela com busca e ordenação
│   ├── assets/fontes/*.woff2      # Reckless Neue (marca)
│   └── assets/*.png|jpg           # marca, retrato, Open Graph
├── scripts/gera_dados.py          # gera as bases abertas e suas páginas
├── _kit_marca/                    # kit do designer (FORA do publish dir)
└── netlify.toml
```

> **Nada de material pesado dentro de `site/`** se não for para servir ao público.
> O kit de marca já esteve publicado por engano em `/geral/` (118 MB, com fontes
> licenciadas baixáveis). Por isso mora em `_kit_marca/`.

---

## 4. Identidade visual

Paleta e tipografia seguem o **Manual de Marca v.01** (`Downloads/rwg_manual_de_marca.pdf`).

| Papel | Valor |
|---|---|
| Azul primário | **#003097** (Pantone 293 C) |
| Azul claro (dado) | **#03A9F4** (Light Blue 500) |
| Tinta | **#1A1A1A** (Pantone Neutral Black C) |

**Sistema tipográfico** (o manual previa marca + um grotesco; foi estendido para leitura
longa, que ele não previa):

| Papel | Fonte |
|---|---|
| Nome e títulos de display | **Reckless Neue Regular** — `--display`, sempre peso 400 |
| Texto de leitura e títulos secundários | **Newsreader** — `--serif` |
| Chapéus, legendas, tabelas, rótulos de dado | **Inter** — `--sans` (no papel da Aktiv Grotesk) |

- A Reckless é servida como woff2 subsetado (~22 KB) de `assets/fontes/`. Licença Desktop
  comprada pela WGSA (pedido Displaay 283195). **Aktiv Grotesk não tem licença** — só
  arquivos trial no kit; por isso o Inter faz o papel dela.
- A Reckless tem **um peso só**: usar sempre `font-weight:400` e
  `font-synthesis-weight:none`, nunca negrito sintético.

---

## 5. Bases abertas (`/dados/`)

O diferencial do site: os dados usados nas análises ficam públicos, com fonte, metodologia
e download.

- `python scripts/gera_dados.py` lê as planilhas de trabalho (fora deste repositório:
  `Desktop/mapa_cidades_MS`, `Desktop/estradas_MS`, `projeto_mapeamento_candGov/inteligencia`)
  e escreve `<slug>.json`, `<slug>.csv`, a página da base e o catálogo.
- **Base nova = uma função no script**, não uma página escrita à mão.
- **Regra:** nada entra sem fonte primária identificada, ano de referência e o lugar exato
  (página do PDF, artigo da norma). Quando existe o arquivo, ele é espelhado em
  `site/dados/fontes/` e aparece como "cópia arquivada" — links de governo somem.
- Quando o número admite leitura torta (caso da renúncia fiscal), a base traz a caixa
  **"Como ler este número"**.

---

## 6. Convenções de conteúdo

- **Tom:** economista institucional, sóbrio, técnico. Nunca populista.
- **Toda afirmação numérica com fonte primária citada** (órgão + documento + ano).
  Fontes preferidas: LOA/LDO, Diário Oficial, Portal da Transparência MS, SICONFI/RREO,
  SEFAZ-MS (base Legato), IBGE, MDIC/ComexStat.
- **Quando o dado não existe, o texto diz que não existe.** Não se estima no lugar.
- **Análise trata da decisão administrativa, nunca da pessoa.** Fato atribuído a
  investigação ou processo entra sempre como atribuição de terceiro, com a fonte —
  nunca imputação própria de crime.
- **Correção se publica no próprio texto, com data.**
- **Cuidado eleitoral:** o autor é pré-candidato. Sem pedido de voto e sem promessa;
  o "como" vai em linguagem condicional e impessoal (Art. 36-A da Lei 9.504/97).

---

## 7. Cuidados técnicos aprendidos

- **Cache:** `/assets/*.css` e `*.js` usam `must-revalidate` — o nome do arquivo é fixo, e
  cache longo deixava quem já visitou com o layout velho. Imagens seguem com 7 dias.
  Os links para CSS e JS carregam `?v=AAAAMMDD`: **ao mexer neles, atualize a versão**
  (nas páginas escritas à mão e em `scripts/gera_dados.py`) para quem já visitou receber
  o arquivo novo na hora.
- O painel da capa lê `site/dados/indicadores.json`; o JSON **precisa estar dentro da pasta
  publicada** (já esteve na raiz e o painel ficou quebrado no ar).
- Formulário de assinatura usa **Netlify Forms** (`data-netlify="true"` + campo
  `form-name`); os envios aparecem no painel do Netlify.

---

## 8. Regra de segurança

**Nunca** versionar token, senha ou credencial. Autenticação do GitHub por token, via Git
Credential Manager.
