# -*- coding: utf-8 -*-
"""
Gera os arquivos abertos do painel de dados do site (site/dados/*.json e *.csv)
a partir das bases de trabalho que ficam fora deste repositorio.

Uso:
    python scripts/gera_dados.py

Cada base vira tres coisas:
  - <slug>.json  -> metadados (fonte, ano, metodologia) + linhas, lido pelas paginas
  - <slug>.csv   -> download direto, separador ";" e BOM (abre no Excel em pt-BR)
  - uma entrada em catalogo.json, que alimenta a pagina /dados/

Regra do projeto: nada entra aqui sem fonte primaria identificada e ano de
referencia. Se a fonte nao estiver clara, a base nao e publicada.
"""

import csv
import io
import json
import os
import unicodedata
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAIDA = os.path.join(RAIZ, "site", "dados")

# --- bases de trabalho (fora do repositorio do site) ------------------------
DESKTOP = r"C:\Users\renat\OneDrive\Desktop"
F_MUNICIPIOS = os.path.join(DESKTOP, "mapa_cidades_MS", "dados", "municipios_ms.csv")
F_ESTADUAIS = os.path.join(DESKTOP, "estradas_MS", "dados", "estaduais_enriq.csv")
F_FEDERAIS = os.path.join(DESKTOP, "estradas_MS", "dados", "federais_enriq.csv")
F_RENUNCIA = os.path.join(DESKTOP, "projeto_mapeamento_candGov", "inteligencia",
                          "documentos_oficiais", "loa_ldo",
                          "renuncia_LDO2026_demonstrativo7.json")

HOJE = date.today().isoformat()


# --- utilidades -------------------------------------------------------------
def le_csv(caminho):
    with io.open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def escreve(slug, meta, colunas, linhas):
    """Grava <slug>.json e <slug>.csv e devolve a entrada de catalogo."""
    os.makedirs(SAIDA, exist_ok=True)
    meta = dict(meta)
    meta.update({"slug": slug, "linhas": len(linhas), "gerado_em": HOJE,
                 "colunas": colunas})

    with io.open(os.path.join(SAIDA, slug + ".json"), "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "dados": linhas}, f, ensure_ascii=False, indent=1)

    with io.open(os.path.join(SAIDA, slug + ".csv"), "w", encoding="utf-8-sig",
                 newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([c["titulo"] for c in colunas])
        for r in linhas:
            w.writerow([r.get(c["campo"], "") for c in colunas])

    print("  {0:<22} {1:>4} linhas".format(slug, len(linhas)))
    return meta


def titulo_setor(s):
    """Repoe acentos dos setores CNAE do demonstrativo (o PDF vem sem)."""
    mapa = {
        "Agricultura, Pecuaria, Producao Florestal, Pesca e Aquicultura":
            "Agricultura, pecuária, produção florestal, pesca e aquicultura",
        "Industrias Extrativas": "Indústrias extrativas",
        "Industrias de Transformacao": "Indústrias de transformação",
        "Eletricidade e Gas": "Eletricidade e gás",
        "Agua, Esgoto, Atividades de Gestao de Residuos e Descontaminacao":
            "Água, esgoto e gestão de resíduos",
        "Construcao": "Construção",
        "Comercio; Reparacao de Veiculos Automotores e Motocicletas":
            "Comércio e reparação de veículos",
        "Comercio; Reparacao de Veiculos Automotores E Motocicletas":
            "Comércio e reparação de veículos",
        "Transporte, Armazenagem e Correio": "Transporte, armazenagem e correio",
        "Alojamento e Alimentacao": "Alojamento e alimentação",
        "Informacao e Comunicacao": "Informação e comunicação",
        "Atividades Financeiras, de Seguros E Servicos Relacionados":
            "Atividades financeiras e de seguros",
        "Atividades Imobiliarias": "Atividades imobiliárias",
        "Atividades Profissionais, Cientificas e Tecnicas":
            "Atividades profissionais, científicas e técnicas",
        "Educacao": "Educação",
        "Saude Humana e Servicos Sociais": "Saúde humana e serviços sociais",
        "Artes, Cultura, Esporte e Recreacao": "Artes, cultura, esporte e recreação",
        "Outras Atividades de Servicos": "Outras atividades de serviços",
        "Servicos Domesticos": "Serviços domésticos",
    }
    return mapa.get(s, s)


def titulo_modalidade(m):
    return {
        "Isencao": "Isenção",
        "Cred. Presumido/Outorgado": "Crédito presumido/outorgado",
        "Modificacao de BC": "Modificação da base de cálculo",
        "Anistia": "Anistia",
    }.get(m, m)


# --- 1. municipios ----------------------------------------------------------
def base_municipios():
    colunas = [
        {"campo": "municipio", "titulo": "Município", "tipo": "texto"},
        {"campo": "quadrante", "titulo": "Região", "tipo": "texto"},
        {"campo": "populacao", "titulo": "População (2022)", "tipo": "inteiro"},
        {"campo": "pib", "titulo": "PIB (2023, R$)", "tipo": "inteiro"},
        {"campo": "pib_per_capita", "titulo": "PIB per capita (R$)", "tipo": "inteiro"},
        {"campo": "receita", "titulo": "Receita do município (2024, R$)", "tipo": "inteiro"},
        {"campo": "receita_per_capita", "titulo": "Receita por habitante (R$)", "tipo": "inteiro"},
        {"campo": "cod_ibge", "titulo": "Código IBGE", "tipo": "texto"},
    ]
    regiao = {"NE": "Nordeste", "NO": "Noroeste", "SO": "Sudoeste", "SE": "Sudeste"}
    linhas = []
    for r in le_csv(F_MUNICIPIOS):
        pop = int(float(r["populacao_2022"]))
        pib = int(float(r["pib_2023_reais"]))
        rec = int(float(r["receita_bruta_2024"]))
        linhas.append({
            "municipio": r["municipio"],
            "quadrante": regiao.get(r["quadrante"], r["quadrante"]),
            "populacao": pop,
            "pib": pib,
            "pib_per_capita": round(pib / pop) if pop else "",
            "receita": rec,
            "receita_per_capita": round(rec / pop) if pop else "",
            "cod_ibge": r["cod_ibge"],
        })
    linhas.sort(key=lambda x: -x["populacao"])

    meta = {
        "titulo": "Os 79 municípios de Mato Grosso do Sul",
        "resumo": "População, PIB, PIB per capita e receita orçamentária de cada "
                  "município do estado, com o valor por habitante calculado.",
        "fontes": [
            "IBGE — Censo 2022 (SIDRA, tabela 4714): população",
            "IBGE — PIB dos municípios 2023 (SIDRA, tabela 5938): PIB a preços correntes",
            "Tesouro Nacional / Siconfi — DCA 2024, Anexo I-C: total das receitas",
        ],
        "metodologia": "Base montada a partir das APIs oficiais do IBGE e do Siconfi. "
                       "A soma das populações fecha com o total do Censo 2022 do MS "
                       "(2.757.013 habitantes). PIB per capita e receita por habitante "
                       "são cálculo próprio: valor dividido pela população de 2022 — "
                       "como as referências são de anos diferentes (PIB 2023, receita "
                       "2024, população 2022), esses dois campos são aproximações úteis "
                       "para comparação entre municípios, não valores oficiais.",
        "referencia": "População 2022 · PIB 2023 · Receita 2024",
    }
    return escreve("municipios-ms", meta, colunas, linhas)


# --- 2. rodovias ------------------------------------------------------------
def base_rodovias():
    colunas = [
        {"campo": "rodovia", "titulo": "Rodovia", "tipo": "texto"},
        {"campo": "jurisdicao", "titulo": "Jurisdição", "tipo": "texto"},
        {"campo": "origem", "titulo": "Origem", "tipo": "texto"},
        {"campo": "destino", "titulo": "Destino", "tipo": "texto"},
        {"campo": "pavimentacao", "titulo": "Situação", "tipo": "texto"},
        {"campo": "pct_pav", "titulo": "% pavimentado", "tipo": "decimal"},
        {"campo": "n_cidades", "titulo": "Cidades no trajeto", "tipo": "inteiro"},
        {"campo": "cidades_trajeto", "titulo": "Trajeto", "tipo": "texto"},
    ]
    linhas = []
    for r in le_csv(F_ESTADUAIS):
        linhas.append({
            "rodovia": r["rodovia"], "jurisdicao": "Estadual",
            "origem": r["origem"], "destino": r["destino"],
            "pavimentacao": r["pavimentacao"],
            "pct_pav": float(r["pct_pav"]) if r.get("pct_pav") else "",
            "n_cidades": int(r["n_cidades"]) if r.get("n_cidades") else "",
            "cidades_trajeto": r["cidades_trajeto"],
        })
    for r in le_csv(F_FEDERAIS):
        linhas.append({
            "rodovia": r["rodovia"], "jurisdicao": "Federal",
            "origem": r["origem"], "destino": r["destino"],
            "pavimentacao": r["pavimentacao"],
            "pct_pav": float(r["pct_pav"]) if r.get("pct_pav") else "",
            "n_cidades": int(r["n_cidades"]) if r.get("n_cidades") else "",
            "cidades_trajeto": r["cidades_trajeto"],
        })

    meta = {
        "titulo": "A malha rodoviária de Mato Grosso do Sul",
        "resumo": "As rodovias estaduais e federais que cortam o estado, com origem, "
                  "destino, cidades atendidas e a situação de pavimentação de cada uma.",
        "fontes": [
            "AGESUL — Sistema Rodoviário Estadual (SRE-MS), edição 2026",
            "OpenStreetMap — traçado e extensão dos trechos, para o cálculo do percentual pavimentado",
        ],
        "metodologia": "As rodovias e seus trechos vêm do SRE-MS 2026. O percentual "
                       "pavimentado é cálculo próprio: sobre o traçado de cada rodovia no "
                       "OpenStreetMap, mede-se a extensão com revestimento asfáltico "
                       "declarado em relação à extensão total mapeada. É uma estimativa "
                       "de base colaborativa: serve para comparar rodovias entre si e "
                       "indicar onde olhar, não substitui levantamento de campo.",
        "referencia": "SRE-MS 2026 · OSM consultado em 2026",
    }
    return escreve("rodovias-ms", meta, colunas, linhas)


# --- 3. renuncia fiscal -----------------------------------------------------
def base_renuncia():
    colunas = [
        {"campo": "setor", "titulo": "Setor (CNAE)", "tipo": "texto"},
        {"campo": "modalidade", "titulo": "Modalidade", "tipo": "texto"},
        {"campo": "v2026", "titulo": "2026 (R$)", "tipo": "inteiro"},
        {"campo": "v2027", "titulo": "2027 (R$)", "tipo": "inteiro"},
        {"campo": "v2028", "titulo": "2028 (R$)", "tipo": "inteiro"},
    ]
    bruto = json.load(io.open(F_RENUNCIA, encoding="utf-8"))
    linhas = []
    for r in bruto:
        linhas.append({
            "setor": titulo_setor(r["setor"]),
            "modalidade": titulo_modalidade(r["mod"]),
            "v2026": r["v"][0], "v2027": r["v"][1], "v2028": r["v"][2],
        })
    linhas.sort(key=lambda x: -x["v2026"])
    total = sum(x["v2026"] for x in linhas)

    meta = {
        "titulo": "Renúncia fiscal de MS em 2026, por setor e modalidade",
        "resumo": "As 58 linhas do demonstrativo oficial de renúncia de receita: "
                  "quanto o estado deixa de arrecadar em cada setor, por tipo de "
                  "benefício, com a projeção para 2027 e 2028.",
        "fontes": [
            "Lei 6.452 (LDO 2026) — Anexo de Metas Fiscais, Demonstrativo 7: "
            "Estimativa e Compensação da Renúncia de Receita, páginas 10 e 11",
        ],
        "metodologia": "As 58 linhas foram extraídas do PDF oficial da LDO e conferidas "
                       "contra o total impresso no próprio demonstrativo. Os nomes dos "
                       "setores seguem a classificação CNAE usada pelo documento; a "
                       "acentuação foi reposta. Total de 2026: R$ {0:,.0f}."
                       .format(total).replace(",", "."),
        "referencia": "LDO 2026 (exercício de 2026, com projeção 2027–2028)",
        "leitura": "Este número não deve ser lido como 'dinheiro desviado' nem como "
                   "'dinheiro disponível para gastar'. A renúncia soma coisas muito "
                   "diferentes: imunidade constitucional (como a exportação, que responde "
                   "por boa parte do agro), política deliberadamente pró-consumidor (a "
                   "cesta básica entra em 'modificação da base de cálculo') e benefício "
                   "discricionário concedido caso a caso (o crédito presumido). A "
                   "discussão pública útil é sobre a terceira categoria — e sobre a "
                   "ausência de um relatório que mostre o que cada beneficiário entregou "
                   "em troca.",
    }
    return escreve("renuncia-fiscal-ms-2026", meta, colunas, linhas)


# --- 4. ICMS na gondola -----------------------------------------------------
# Conferido item a item no texto oficial da SEFAZ-MS (base Legato), nao em
# noticia. Cada linha traz o dispositivo que fixa a carga.
ICMS_ITENS = [
    ("Arroz", "Cesta básica", 7.0, "Anexo I, art. 52 (redução de base de 58,824%)"),
    ("Feijão", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Óleo de soja", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Café torrado e moído", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Sal", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Farinha de mandioca", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Farinha de milho e fubá", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Erva-mate e chá mate", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Vinagre", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Banha de porco", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Peixe", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Sabonete em barra", "Higiene", 7.0, "Anexo I, art. 52"),
    ("Mel produzido em MS", "Cesta básica", 7.0, "Anexo I, art. 52"),
    ("Verduras, legumes e frutas in natura", "Hortifrúti", 7.0,
     "Anexo I, Subanexo XIII"),
    ("Ovos", "Hortifrúti", 7.0,
     "Anexo I, Subanexo XIII — isento apenas na venda direta do produtor ao consumidor (art. 2º)"),
    ("Carne bovina e bubalina", "Carnes", 4.0,
     "Decreto 12.056/2006, art. 7º (redução de base de 76,471%)"),
    ("Carne suína", "Carnes", 7.0, "Decreto 12.056/2006, art. 8º"),
    ("Frango e demais aves", "Carnes", 7.0, "Decreto 12.056/2006, art. 9º"),
    ("Leite produzido em MS", "Cesta básica", 0.0, "Anexo I, art. 30 — isento"),
    ("Farinha de trigo", "Cesta básica", 12.0, "Anexo I, art. 53, I"),
    ("Pão francês e pão de forma", "Cesta básica", 12.0, "Anexo I, art. 53, I"),
    ("Açúcar", "Cesta básica", 17.0,
     "Sem benefício previsto — alíquota geral do RICMS, art. 41, III, 'a'"),
    ("Macarrão e massas", "Cesta básica", 17.0,
     "Sem benefício previsto — alíquota geral do RICMS, art. 41, III, 'a'"),
]


def base_icms():
    colunas = [
        {"campo": "item", "titulo": "Item", "tipo": "texto"},
        {"campo": "grupo", "titulo": "Grupo", "tipo": "texto"},
        {"campo": "carga", "titulo": "ICMS na gôndola (%)", "tipo": "decimal"},
        {"campo": "base_legal", "titulo": "Base legal", "tipo": "texto"},
    ]
    linhas = [{"item": i, "grupo": g, "carga": c, "base_legal": b}
              for (i, g, c, b) in ICMS_ITENS]
    linhas.sort(key=lambda x: (x["carga"], x["item"]))

    meta = {
        "titulo": "Quanto de ICMS vai em cada item da cesta",
        "resumo": "A carga efetiva de ICMS na venda ao consumidor final, item a item, "
                  "com o dispositivo legal que fixa cada percentual.",
        "fontes": [
            "SEFAZ-MS — RICMS, Anexo I (arts. 30, 52 e 53 e Subanexo XIII)",
            "SEFAZ-MS — Decreto 12.056/2006 (carnes), arts. 6º a 9º",
            "SEFAZ-MS — RICMS, art. 41, III, 'a' (alíquota geral de 17%)",
        ],
        "metodologia": "Cada linha foi conferida no texto oficial da norma, na base "
                       "Legato da SEFAZ-MS, e não em fonte jornalística. Os percentuais "
                       "de 7% (cesta e hortifrúti) e 4% (carne bovina) resultam de "
                       "redução de base de cálculo, às vezes combinada com diferimento e "
                       "crédito presumido: o valor informado é a carga final na saída ao "
                       "consumidor. Os benefícios da cesta e das carnes estão prorrogados "
                       "até 31/12/2026 pelo Decreto 16.753/2026.",
        "referencia": "Legislação vigente em 2026 · alíquota geral de MS: 17%",
        "leitura": "Dois pontos que costumam se perder no debate: 7% não é isenção — há "
                   "estado que zerou a cesta — e itens básicos como açúcar e macarrão "
                   "pagam a alíquota cheia de 17%, enquanto a carne bovina paga 4%.",
    }
    return escreve("icms-gondola-ms", meta, colunas, linhas)


# --- paginas HTML -----------------------------------------------------------
CABECA = u"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo} — Economista Renato Gomes</title>
<meta name="description" content="{resumo}">
<link rel="canonical" href="https://economistarenato.com.br/dados/{canonico}">
<meta property="og:type" content="website">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Economista Renato Gomes">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{resumo}">
<meta property="og:url" content="https://economistarenato.com.br/dados/{canonico}">
<meta property="og:image" content="https://economistarenato.com.br/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{r}assets/monograma-azul.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,300..600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{r}assets/estilo.css">
</head>
<body>

<header>
  <div class="env">
    <div class="cabecalho" style="padding:18px 0 14px">
      <a href="{r}"><img class="marca" src="{r}assets/marca-wordmark.png" alt="Renato W. Gomes — Economista" style="width:min(240px,60vw)"></a>
    </div>
  </div>
  <nav class="secoes">
    <div class="env">
      <a href="{r}">Capa</a>
      <a href="{r}artigo/estreia/">A coluna</a>
      <a href="{r}dados/" class="ativo">Bases abertas</a>
      <a href="{r}#pautas">Pautas</a>
      <a href="{r}sobre/">Sobre</a>
    </div>
  </nav>
</header>
"""

RODAPE = u"""
<footer>
  <div class="env">
    <div class="rodape-fim" style="margin-top:0;border:none;padding-top:0">
      <span>© 2026 Renato W. Gomes · Economista, CORECON-MS 1297 · Campo Grande, MS</span>
      <span>Conteúdo de análise e opinião pessoal. Não constitui propaganda eleitoral.</span>
    </div>
  </div>
</footer>

</body>
</html>
"""


def data_br(iso):
    meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
    a, m, d = iso.split("-")
    return "{0} de {1} de {2}".format(int(d), meses[int(m) - 1], a)


def pagina_base(meta):
    """Uma pagina por base, em site/dados/<slug>/index.html."""
    pasta = os.path.join(SAIDA, meta["slug"])
    os.makedirs(pasta, exist_ok=True)

    fontes = "".join(u"<li>{0}</li>".format(f) for f in meta["fontes"])
    leitura = u""
    if meta.get("leitura"):
        leitura = (u'<div class="caixa-leitura"><h3>Como ler este número</h3>'
                   u'<p>{0}</p></div>').format(meta["leitura"])

    corpo = u"""
<article class="largura-dados">
  <div class="texto-dados" style="margin-top:34px">
    <span class="chapeu dado">Base aberta</span>
    <h1 class="tit" style="font-size:clamp(1.9rem,3.6vw,2.6rem);font-weight:500;letter-spacing:-.02em;line-height:1.1">{titulo}</h1>
    <p class="olho olho-xl">{resumo}</p>
  </div>

  <dl class="ficha">
    <div><dt>Linhas</dt><dd>{linhas}</dd></div>
    <div><dt>Referência</dt><dd>{referencia}</dd></div>
    <div><dt>Atualizado</dt><dd>{atualizado}</dd></div>
    <div><dt>Licença</dt><dd>Uso livre com crédito</dd></div>
  </dl>

  <div id="tabela" data-base="{slug}"></div>

  <div class="texto-dados" style="margin-top:36px">
    {leitura}
    <h2 class="tit tit-g" style="margin-top:34px">Metodologia</h2>
    <p class="olho">{metodologia}</p>

    <h2 class="tit tit-g" style="margin-top:30px">Fontes</h2>
    <ul class="olho" style="margin-left:1.1em">{fontes}</ul>

    <div class="citar">
      <h3>Como citar</h3>
      <code>GOMES, Renato W. <b>{titulo}</b>. economistarenato.com.br, {atualizado}.
      Disponível em: https://economistarenato.com.br/dados/{slug}/</code>
    </div>

    <p class="nota-legal">Base montada a partir de documentos públicos. Se você
    encontrar divergência entre um valor daqui e a fonte oficial, escreva: a
    correção é publicada com data, e o arquivo é regerado.</p>
  </div>
</article>

<script src="{r}assets/tabela.js"></script>
"""
    html = (CABECA.format(titulo=meta["titulo"], resumo=meta["resumo"],
                          canonico=meta["slug"] + "/", r="../../") +
            corpo.format(titulo=meta["titulo"], resumo=meta["resumo"],
                         linhas=meta["linhas"], referencia=meta["referencia"],
                         atualizado=data_br(meta["gerado_em"]), slug=meta["slug"],
                         metodologia=meta["metodologia"], fontes=fontes,
                         leitura=leitura, r="../../") +
            RODAPE)
    with io.open(os.path.join(pasta, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


def pagina_catalogo(catalogo):
    """Hub em site/dados/index.html."""
    cartoes = u"".join(u"""
    <a class="base-cartao" href="{slug}/">
      <span class="chapeu dado">{referencia}</span>
      <h2 class="tit">{titulo}</h2>
      <p class="olho">{resumo}</p>
      <div class="base-meta"><span><b>{linhas}</b> linhas</span><span>CSV e JSON</span><span>Atualizado em {atualizado}</span></div>
    </a>""".format(slug=b["slug"], titulo=b["titulo"], resumo=b["resumo"],
                   linhas=b["linhas"], referencia=b["referencia"],
                   atualizado=data_br(b["gerado_em"])) for b in catalogo)

    corpo = u"""
<main class="largura-dados">
  <div class="texto-dados" style="margin-top:34px">
    <span class="chapeu dado">Bases abertas</span>
    <h1 class="tit" style="font-size:clamp(2rem,3.8vw,2.8rem);font-weight:500;letter-spacing:-.02em;line-height:1.1">Os dados de Mato Grosso do Sul, abertos para quem quiser conferir</h1>
    <p class="olho olho-xl">Toda análise publicada aqui sai de um documento público. Em vez de
    guardar as planilhas, elas ficam nesta página: com a fonte, o ano de referência, a
    metodologia e o arquivo para baixar. Jornalista, pesquisador, vereador, estudante ou
    curioso — use à vontade, o crédito basta.</p>
  </div>

  <div class="catalogo">{cartoes}</div>

  <div class="texto-dados" style="margin-top:30px">
    <p class="olho">Cada base traz a norma ou o documento de origem em cada linha, sempre que
    a informação existir. Quando um dado não é publicado pelo poder público, a página diz
    isso em vez de estimar.</p>
    <p class="nota-legal">Encontrou divergência entre um valor daqui e a fonte oficial?
    Escreva. A correção é publicada com data e o arquivo é regerado.</p>
  </div>
</main>
"""
    html = (CABECA.format(
                titulo=u"Bases abertas sobre Mato Grosso do Sul",
                resumo=(u"Orçamento, renúncia fiscal, municípios, rodovias e carga de ICMS: "
                        u"as bases usadas nas análises, com fonte, metodologia e download."),
                canonico=u"", r="../") +
            corpo.format(cartoes=cartoes) + RODAPE)
    with io.open(os.path.join(SAIDA, "index.html"), "w", encoding="utf-8") as f:
        f.write(html)


# --- catalogo ---------------------------------------------------------------
def main():
    print("Gerando bases abertas em site/dados/ ...")
    catalogo = [base_renuncia(), base_municipios(), base_rodovias(), base_icms()]
    with io.open(os.path.join(SAIDA, "catalogo.json"), "w", encoding="utf-8") as f:
        json.dump({"atualizado_em": HOJE, "bases": catalogo}, f,
                  ensure_ascii=False, indent=1)
    for b in catalogo:
        pagina_base(b)
    pagina_catalogo(catalogo)
    print("Catálogo com {0} bases + paginas HTML.".format(len(catalogo)))


if __name__ == "__main__":
    main()
