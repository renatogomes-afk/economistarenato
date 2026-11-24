# Acervo técnico (/tech/<periódico>/<ano>/)

Gerado por `scripts/gera_site.py` (funções `gera_tech_acervo`, `pagina_tech_periodico`, `pagina_tech_ano`).

- `periodicos.json`: um item por periódico (`slug`, `nome`, `sigla`, `periodo` [início, fim], `editora`,
  `descricao`, `fonte`, `fonte_url`). Cada periódico aparece em `/tech/#acervo` e ganha a página `/tech/<slug>/`,
  com a grade "Por ano" (azul = analisado, cinza = em breve).
- `<slug>/<ano>.md`: a análise do ano. O primeiro `# Título` vira o título da página; o resto é Markdown simples
  (`##`/`###`, parágrafos, listas com `- `, `**negrito**`, `*itálico*`).

**Ano novo:** salvar `scripts/tech/<slug>/<ano>.md` e rodar `python scripts/gera_site.py`. Links de ano
anterior/seguinte, grade de anos e sitemap se atualizam sozinhos.
**Periódico novo:** acrescentar o item em `periodicos.json` (e a pasta `<slug>/` quando houver o primeiro ano).

Regras de conteúdo: fatos de época só do texto dos artigos; história posterior só com marcos bem estabelecidos;
a parte de investimentos é histórica e didática, sem recomendação.

## Modelo editorial de cada ano (padrão para todos os periódicos)

Cabeçalho com as edições do ano e a lista completa de artigos (título, autor). Depois três camadas, com o mesmo peso:

1. **Reportagem** — lead forte (cena ou fato concreto), narrativa, contexto da época, citações curtas traduzidas
   com o original em inglês entre parênteses.
2. **Análise econômica** — organização industrial, regulação, P&D, custos da rede, desdobramentos até hoje.
3. **Research de investimentos** — no formato de relatório de research de banco (sem citar nomes ou marcas de
   bancos): Principais conclusões (3–5 tópicos), Tese de investimento, Vetores de valor, Riscos, Catalisadores,
   Horizonte, Quadro-resumo; depois Retrospectiva (o que aconteceu) e Lições para hoje. Linguagem seca. Sempre
   com o aviso de que é análise histórica, sem recomendação.

Fecha com "Na minha leitura" e a linha "Fonte:". Tamanho: cerca de 2.000 a 2.500 palavras.
