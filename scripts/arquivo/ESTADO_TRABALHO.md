# Estado do trabalho — Arquivo (atualizado em 21/11/2026)

## Publicado
- Arquivo até a **nº 210** (American Economic Review, dezembro de 1928), com página própria para todo artigo em 1926–1928.
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
0. **PONTO DE RETOMADA (21/11/2026):** AER **1928 publicada** (nº 206–210: março, 40ª reunião, junho, setembro, dezembro;
   36 páginas próprias). Próximo: **1929** (03_19_1, 03 supplement = 41ª reunião, 06, 09, 12), mesmo método:
   OCR Tesseract por página (`_tesseract\tools\reocr.py`, só as páginas de artigos nos números regulares), `join.py`,
   brief `BRIEF_REDATOR.md`, validador `valida_aer.py`; redatores Opus (até 2 em paralelo, autorizado em 21/11/2026), suplemento
   dividido em duas partes. Material de 1928 (OCR, joins, scripts de cada edição) em
   `Downloads\AEA_historico\The American Economic Review\The American Economic Review (1911-1929)\1928\_tesseract\`.
   Manual de 1928 baixado do JSTOR (20/11/2026): `1928\AER_1928_vol18_no2_i331356.pdf` (ainda sem edição no site).
   Depois de 1929: a passada de volta (item 3 + item 4).
1. **1926–1928**: publicados (nº 195–210).
2. **1927–1929**: arquivos baixados e conferidos em
   `Downloads\AEA_historico\The American Economic Review\The American Economic Review (1911-1929)\<ano>\_archive_sim\`
   (pasta renomeada para (1911-1929) em 20/11/2026; indice.csv e edicoes.csv atualizados).
3. **Completar páginas próprias** nas edições feitas antes da regra nova, em ordem: 189–192 (1925),
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
