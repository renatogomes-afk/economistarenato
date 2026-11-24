# CLAUDE.md — economistarenato.com.br

> Contexto do projeto para o Claude Code. Fica na raiz do repositório e é lido
> automaticamente ao iniciar.

---

## 1. O que é este projeto

**Publicação editorial** de **Renato Wanderley Gomes** — economista (CORECON-MS nº 1297),
sócio-fundador da WGSA. (Desde 08/11/2026 o autor **não é mais pré-candidato**.)

Posicionamento (reorganização de 08/11/2026): **"Economia pelas fontes"** — clássicos e
debates da economia lidos no original e comentados em português (seção **Arquivo**, começando
pelas publicações da American Economic Association, 1886–1929, domínio público), contas
públicas com documento oficial (**Análises**) e **Serviços** (consultoria WGSA, palestras,
cursos). Registro de **economista institucional**: toda afirmação numérica com fonte primária
verificável, sempre visível para o leitor.

**Domínio:** `economistarenato.com.br` · **Handle:** `@economistarenato`
**Estratégia:** `projeto_mapeamento_candGov/comunicacao_digital/PLANO_AUTORIDADE_2027_2028.md`

---

**Capa + uma página por interesse (24/11/2026, em revisão):** a raiz é uma capa enigmática (marca, uma frase e
três portas), não divulgada. O marketing vai direto para cada página de entrada, que precisa funcionar sozinha:
`/tech/` (agentes de IA para PMEs, com o contato), `/historia/` (livros comentados: Leituras) e `/economia/`
(periódicos: Arquivo). As páginas internas continuam em `/arquivo/` e `/leituras/`. `/servicos/` redireciona
para `/tech/`. `/bitcoin/` é o piloto público de análise técnica: diário de retornos em
`scripts/bitcoin/diario.csv` (data, retorno_pct, nota; só percentuais, nunca valores em reais) e autores em
`AUTORES_BTC`. Campo Grande e Análises ficam sem link. Newsletter desligada (`assine()` devolve vazio).
Contato: FormSubmit (`FORM_CONTATO`/`EMAIL_CONTATO` em `gera_site.py`), volta para `/obrigado/`.

---

## 2. Stack

- **Site estático** — HTML/CSS/JS puro, sem framework e sem build step.
- **GitHub Pages** (desde 09/11/2026), deploy contínuo do GitHub `renatogomes-afk/economistarenato` (branch `main`,
  workflow `.github/workflows/pages.yml`, publica a pasta `site/`; domínio em `site/CNAME`). O Netlify
  foi abandonado (limite de créditos do plano grátis); `netlify.toml` tem `ignore = "exit 0"`.
  Publicar = `git add . && git commit && git push` → ~1 min.
- **Sem CMS, sem servidor, sem banco.**

---

## 3. Estrutura

```
economistarenato/
├── site/                          # ← PUBLISH DIR do Netlify (GERADO — não editar à mão)
│   ├── index.html                 # início
│   ├── arquivo/index.html         # Arquivo · Clássicos comentados
│   ├── arquivo/<slug>/index.html  # uma página por edição/obra comentada
│   ├── analises/index.html        # contas públicas (em preparação)
│   ├── servicos/index.html        # consultoria, palestras, cursos + formulário "contato"
│   ├── sobre/index.html           # trajetória e método
│   ├── obrigado/index.html        # retorno dos formulários (Netlify Forms)
│   ├── sitemap.xml
│   └── assets/                    # estilo.css, fontes, marca, fotos
├── scripts/gera_site.py           # GERA O SITE INTEIRO (cabeçalho, menu e rodapé num lugar só)
├── scripts/arquivo/edicoes.json   # conteúdo do Arquivo: edições, resumos, fontes
├── scripts/gera_dados.py          # (antigo) gerador das bases abertas — páginas removidas
├── _kit_marca/                    # kit do designer (FORA do publish dir)
└── netlify.toml
```

- **Edição nova no Arquivo** = um item em `scripts/arquivo/edicoes.json` + `python scripts/gera_site.py`.
- Mudou menu, cabeçalho ou rodapé? Muda em `gera_site.py` e regera tudo.
- Nada de material pesado dentro de `site/` se não for para servir ao público (PDFs do Arquivo
  ficam no Internet Archive/JSTOR — o site só aponta).

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

- **Assinatura (24/11/2026):** o logo do site é o vetor oficial do manual (`_kit_marca/.../_vetor/rwg_marca_01.ai`
  e `rwg_marca_01_tag.ai`, página 6, preto sobre branco), salvo em `scripts/arquivo/_marca_lockup.svg` e
  `_marca_lockup_tag.svg`: símbolo + **"Renato / W. Gomes"**, com o tag **ECONOMISTA** embaixo só no cabeçalho grande.
  Nunca digitar o nome em fonte nem trocar por "Economista Renato Gomes".

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
- **Arquivo:** citar sempre a fonte (JSTOR Early Journal Content / Internet Archive); não usar
  "AEA" como nome de marca; nota "sem afiliação com a American Economic Association".

---

### Arquivo: modelo editorial e profundidade mínima (aprovado em 08/11/2026)

**Modelo híbrido** (obrigatório a partir das edições com vários artigos, como a American Economic Review):
- **Página da edição = hub:** visão geral da edição + lista de todos os artigos (campo `artigos` em
  `edicoes.json`), cada um com link para o original.
- **Artigo relevante ganha página comentada própria** em `/arquivo/<edicao>/<artigo>/` (campo
  `ensaio_slug` no artigo). O texto do comentário fica na própria edição, na lista `comentarios`
  (slug, titulo, titulo_original, autores, paginas, jstor, chamada, blocos, glossario, hoje); imagem em
  `site/assets/arquivo/<edicao>--<artigo>.jpg`. Gerado por `pagina_comentario()` em `gera_site.py`.
- **Regra de 15/11/2026 (American Economic Review):** a página da edição é uma resenha contínua com uma seção
  de 300–400 palavras por artigo; **todo artigo principal e toda comunicação ganham página própria** com link
  "Ler o comentário completo" (600–800 palavras para os curtos, 1.200–1.500 para os longos). Resenhas de livros,
  notas e listas ficam só na lista do fim. Nas reuniões anuais, página própria para todo paper. Resenhas, notas e "new books" ficam só no hub.
- Edições de monografia única (1886–1887) continuam como página única.

**Profundidade mínima (mínimos flexíveis, não rígidos):**
| Formato | Tamanho |
|---|---|
| Página de artigo comentado | ≥ ~900 palavras (≈ 5 min), modelo padrão |
| Ensaio principal (`"ensaio": true`, aparece em /ensaios/) | 1.500–2.000 palavras |
| Hub da edição | visão geral ≥ 200 palavras + 60–120 palavras de parágrafo real por artigo listado; itens menores (resenhas, notas, new books) podem ficar agrupados, uma linha cada |
| Nota "Então × Agora" | 400–600 palavras |

- **Ordem:** estritamente cronológica (decisão de 08/11/2026): primeiro as Publications (1886–1907), depois o Quarterly e o Economic Bulletin (1908–1910), depois a American Economic Review (1911–1929; de 1923 em diante, a partir das digitalizações de número completo do Internet Archive). Numeração contínua, sem lacunas.
- **Preservar a história do documento (decisão de 15/11/2026):** o que o autor diz sobre grupos étnicos, raciais ou nacionais (teses, opiniões e números legíveis) entra na resenha de forma descritiva e atribuída ("segundo Willcox…"), sem comentário, ressalva ou endosso na voz do site. Nada se omite por cautela; só números/nomes ilegíveis no OCR ficam de fora.
- **Nunca encher linguiça:** artigo que não sustenta ~900 palavras de análise real fica só no hub.
- Padrão de redação de toda página: abrir com cena ou fato concreto; citação traduzida com o original
  entre parênteses; um número-chave por parágrafo (o resto em caixa); jargão explicado na primeira
  aparição ou no glossário; subtítulos em forma de pergunta; 1–2 parágrafos "Na minha leitura"
  separados; tempo de leitura calculado automaticamente (200 palavras/min).
- Todo fato, número, nome, data e citação conferido no documento original; na dúvida, fica de fora.
  O registro da conferência vai para `scripts/arquivo/verificacao.json` (não publicado).

---

## 7. Cuidados técnicos aprendidos

- **Cache:** `/assets/*.css` e `*.js` usam `must-revalidate` — o nome do arquivo é fixo, e
  cache longo deixava quem já visitou com o layout velho. Imagens seguem com 7 dias.
  Os links para CSS e JS carregam `?v=AAAAMMDD`: **ao mexer neles, atualize a versão**
  (em `scripts/gera_site.py`, constante `CSS_V`) para quem já visitou receber
  o arquivo novo na hora.
- Formulários: **Netlify Forms** NÃO funcionam no GitHub Pages. O contato (/tech) usa **FormSubmit** (24/11/2026).
  A newsletter está desligada.

---

## 8. Regra de segurança

**Nunca** versionar token, senha ou credencial. Autenticação do GitHub por token, via Git
Credential Manager.
