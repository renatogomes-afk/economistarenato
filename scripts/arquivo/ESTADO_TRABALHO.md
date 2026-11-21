# Estado do trabalho — Arquivo (atualizado em 21/11/2026)

## Publicado
- Arquivo até a **nº 215** (American Economic Review, dezembro de 1929), com página própria para todo artigo em 1926–1929.
- **Economic Studies completa**: ES 1–25 (1896–1899), série própria, já com a regra de preservar a história do documento. 1926 completo, já com página própria para todo artigo.
- 1923–1925 vêm das digitalizações de número completo do Internet Archive (campo `archive_id`; ids internos `ia-…`).
- Página `/arquivo/eua/` organizada por ano (barra de anos por década + seções por ano).

## Regras em vigor (ver CLAUDE.md, seção Arquivo)
- Página da edição = resenha contínua, uma seção de 300–400 palavras por artigo.
- **Desde 15/11/2026: todo artigo principal e toda comunicação têm página própria**
  ("Ler o comentário completo"): 600–800 palavras para curtos, 1.200–1.500 para longos.
  Resenhas de livros, notas e listas: só na lista. Reuniões anuais: página para todo paper.
- Redatores no modelo Opus até 1929; um redator por vez (economia de cota, sem perder qualidade);
  conferência completa antes de publicar (números, nomes, citações contra o OCR, mínimos, tom).
- Publicar por ano; relatório curto ao fim de cada ano.

## Em andamento / próximo
0. **PONTO DE RETOMADA (21/11/2026):** AER **1929 publicada** (nº 211–215: março, 41ª reunião, junho, setembro, dezembro;
   41 páginas próprias), com conferência completa por dois conferentes Opus. Fecha o recorte 1886–1929.
   OCR de 1929: Tesseract com limiar 180 e sem filtro de mediana (`reocr180.py`; o limiar 220 de 1928 saiu ruim nesse scan),
   em `...\(1911-1929)\1929\_tesseract\`; joins, briefs e scripts de cada edição (n211–n215) ficaram no scratchpad da sessão.
   **AER 1930 baixada do JSTOR (21/11/2026): 222 PDFs** (março, suplemento da 42ª reunião, junho, setembro, dezembro) em
   `...\(1911-1929)\1930\_artigos\`, com PDF de cada número e linhas em indice.csv/edicoes.csv (estudo pessoal; fora do recorte do site).
   Atenção: IDs curtos do JSTOR (junho 417–470, dezembro 844–893) exigem conferência exata de id no CSV, não por substring.
   Manual de 1928 baixado do JSTOR (20/11/2026): `1928\AER_1928_vol18_no2_i331356.pdf` (ainda sem edição no site).
   **Passada de volta, 1925 publicada (21/11/2026):** nº 189–192 refeitas no formato atual (32 páginas próprias, slugs e ids
   mantidos), com os trechos sobre grupos étnicos/nacionais recolocados e conferência completa. Método: OCR `reocr180.py`
   (em `...\1925\_tesseract\`), pedido `PEDIDO_VOLTA.md` + `BRIEF_REDATOR.md`, versão publicada como ponto de partida.
   Importador: itens com `"tipo": "errata"` ou `"necrologio"` ficam só na lista. Próximo: **1924** (nº 180–188), mesma passada
   (sem as edições novas de 1924, que aguardam o Renato).
1. **1926–1929**: publicados (nº 195–215).
2. **1927–1929**: arquivos baixados e conferidos em
   `Downloads\AEA_historico\The American Economic Review\The American Economic Review (1911-1929)\<ano>\_archive_sim\`
   (pasta renomeada para (1911-1929) em 20/11/2026; indice.csv e edicoes.csv atualizados).
3. **Completar páginas próprias** nas edições feitas antes da regra nova, em ordem: ~~189–192 (1925)~~ (feito em 21/11/2026),
   180–188 (1923–1924), depois 112–179 (1911–1922).

4. **Preservar a história do documento (15/11/2026):** revisar as edições antigas (Publications, Quarterly,
   Bulletin, AER até a nº 200) para recolocar o que os autores dizem sobre grupos étnicos/raciais, descrito e
   atribuído, junto com a passada de volta do item 3. **Confirmado pelo Renato em 15/11/2026.** Prioridade: Economic Studies → AER 1927–1929 → passada de volta.

## Lacunas conhecidas (sem fonte aberta)
- ~~AER, anais da 36ª reunião (março de 1924); manuais da associação de 1924 e 1928.~~ Resolvido em 20/11/2026:
  baixados do JSTOR com o acesso de membro da AEA (40 PDFs): `1924\AER_1924_vol14_no1_i331260.pdf` (36ª reunião, 29 itens),
  `1924\AER_1924_vol14_no2_i331233.pdf` (manual de 1924, 5) e `1928\AER_1928_vol18_no2_i331356.pdf` (manual de 1928, 6), com os
  artigos em `_artigos\` e linhas novas em indice.csv/edicoes.csv. Os anais da 36ª reunião ainda não têm edição no site (entre a nº 185 e a nº 186; entrar exigiria renumerar ou usar número próprio): decisão pendente do Renato.
- Artigos de mar/1923 e mar/1924 baixados do JSTOR à mão só em parte (o resto veio do Internet Archive).

## DECISÃO PENDENTE (Renato)
- **Economic Studies of the AEA (1896–1899)**: série paralela às Publications, 4 volumes (~27 itens),
  nunca entrou no site (não estava no JSTOR Early Journal Content). Download do Internet Archive em
  `Downloads\AEA_historico\Economic Studies of the American Economic Association (1896-1899)\`.
  Opções: (1) inserir na ordem cronológica e renumerar nº 51–194; (2) série própria "ES 1, ES 2…"
  nos anos certos, sem mexer na numeração atual (recomendada).
