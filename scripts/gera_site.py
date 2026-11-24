"""Gera o site inteiro (páginas estáticas) a partir de scripts/arquivo/edicoes.json.

Uso:  python scripts/gera_site.py
Saída: site/index.html, site/arquivo/, site/analises/, site/servicos/, site/sobre/, site/obrigado/,
       site/sitemap.xml
Cabeçalho, menu e rodapé ficam aqui, num lugar só: mexeu aqui, mudou em todas as páginas.
"""
import json, re, os, html, math
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(RAIZ, "site")
DADOS = json.load(open(os.path.join(RAIZ, "scripts", "arquivo", "edicoes.json"), encoding="utf-8"))
# Assinatura oficial (Manual de Marca v.01), vetor tirado de _kit_marca/_vetor/rwg_marca_01*.ai, texto em curvas.
MARCA = open(os.path.join(RAIZ, "scripts", "arquivo", "_marca_lockup.svg"), encoding="utf-8").read().strip()
MARCA_TAG = open(os.path.join(RAIZ, "scripts", "arquivo", "_marca_lockup_tag.svg"), encoding="utf-8").read().strip()
LOGO = open(os.path.join(RAIZ, "scripts", "arquivo", "_logo.svg"), encoding="utf-8").read().strip()
COLECOES = json.load(open(os.path.join(RAIZ, "scripts", "arquivo", "colecoes.json"), encoding="utf-8"))["colecoes"]
_CG = os.path.join(RAIZ, "scripts", "campo-grande", "livro.json")
CG = json.load(open(_CG, encoding="utf-8")) if os.path.exists(_CG) else None
_CGN = os.path.join(RAIZ, "scripts", "campo-grande", "noticias.json")
NOTICIAS_CG = json.load(open(_CGN, encoding="utf-8"))["noticias"] if os.path.exists(_CGN) else []
# Submenus de Campo Grande-MS: (slug, nome no menu, descrição)
SUB_CG = [("livro", "Livro · Minhas propostas para 2028", "O livro em construção, capítulo a capítulo: o diagnóstico de cada tema e as propostas para a cidade."),
          ("situacao-atual", "Situação atual", "Como a cidade está hoje, tema a tema, com o número e a fonte de cada dado."),
          ("noticias", "Notícias importantes", "Os fatos que mexem com a cidade, com a fonte e um comentário curto.")]
DOMINIO = "https://economistarenato.com.br"
CSS_V = "20261124g"
LEMA = "Economia pelas fontes"  # lema antigo, só no Arquivo
FRASE = "Ajudo pequenas e médias empresas a usar IA com retorno medido"
# Formulário de contato via FormSubmit (grátis, sem conta): o 1º envio pede ativação por e-mail.
# Depois da ativação, dá para trocar o e-mail na URL pelo código que o FormSubmit manda, para não expor o endereço.
EMAIL_CONTATO = "renato.gomes@wgsa.com.br"
FORM_CONTATO = f"https://formsubmit.co/{EMAIL_CONTATO}"
SUBLEMA = "Análise econômica com documento na mesa — dos clássicos às contas públicas de hoje"

e = html.escape


def cabeca(titulo, descricao, caminho, rel, tipo="website"):
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titulo)}</title>
<meta name="description" content="{e(descricao)}">
<link rel="canonical" href="{DOMINIO}/{caminho}">
<meta property="og:type" content="{tipo}">
<meta property="og:locale" content="pt_BR">
<meta property="og:site_name" content="Economista Renato Gomes">
<meta property="og:title" content="{e(titulo)}">
<meta property="og:description" content="{e(descricao)}">
<meta property="og:url" content="{DOMINIO}/{caminho}">
<meta property="og:image" content="{DOMINIO}/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{rel}assets/favicon.svg" type="image/svg+xml">
<link rel="alternate icon" href="{rel}assets/monograma-azul.png">
<link rel="apple-touch-icon" href="{rel}assets/favicon-512.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:ital,opsz,wght@0,6..72,300..700;1,6..72,300..600&display=swap" rel="stylesheet">
<link rel="preload" href="{rel}assets/fontes/reckless-neue-regular.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{rel}assets/estilo.css?v={CSS_V}">
</head>
<body>
"""


IG_SVG = '<svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true"><path fill="currentColor" d="M12 2.2c3.2 0 3.6 0 4.8.1 3.3.1 4.8 1.7 4.9 4.9.1 1.3.1 1.6.1 4.8s0 3.6-.1 4.8c-.1 3.2-1.7 4.8-4.9 4.9-1.3.1-1.6.1-4.8.1s-3.6 0-4.8-.1c-3.3-.1-4.8-1.7-4.9-4.9C2.2 15.6 2.2 15.2 2.2 12s0-3.6.1-4.8C2.4 3.9 3.9 2.4 7.2 2.3 8.4 2.2 8.8 2.2 12 2.2zm0 4.8a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0 8.2a3.2 3.2 0 1 1 0-6.4 3.2 3.2 0 0 1 0 6.4zm5.2-9.6a1.2 1.2 0 1 0 0 2.4 1.2 1.2 0 0 0 0-2.4z"/></svg>'

# Menu principal (site minimalista, 24/11/2026). Leituras, Campo Grande, Análises, Ensaios e Notas
# saíram do menu: as páginas continuam geradas, mas sem link na navegação.
MENU = [("tech/", "Tech"), ("bitcoin/", "Bitcoin"), ("historia/", "História"), ("economia/", "Economia"), ("ms/", "MS"), ("sobre/", "Sobre")]


def topo(ativo, rel, completo=True):
    ativo = {"arquivo/": "economia/", "ensaios/": "economia/", "notas/": "economia/", "leituras/": "historia/", "campo-grande/": "ms/", "analises/": "ms/"}.get(ativo, ativo)
    ativo_cls = ' class="ativo"'
    itens = "".join(f'<li><a href="{rel}{h}"{ativo_cls if h == ativo else ""}>{n}</a></li>' for h, n in MENU)
    return f"""<header class="topo-min">
  <div class="env topo-min-barra">
    <a class="marca-lockup compacta" href="{rel}" aria-label="Início">{MARCA}</a>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="menu-principal">Menu <span aria-hidden="true">&#9776;</span></button>
    <nav aria-label="Menu principal">
      <ul class="menu-min" id="menu-principal">
        {itens}
      </ul>
    </nav>
  </div>
</header>
<script>
document.querySelector('.nav-toggle').addEventListener('click',function(){{var m=document.getElementById('menu-principal');var o=m.classList.toggle('aberto');this.setAttribute('aria-expanded',o)}});
</script>
"""


def assine(titulo="", texto=""):
    # Newsletter fora do ar no site minimalista: o formulário (Netlify Forms) não funciona no GitHub Pages.
    return ""


def _assine_antigo(titulo="A carta do economista, no seu e-mail.", texto="Um clássico comentado e uma análise com fonte primária, uma vez por semana. Sem custo e sem spam."):
    return f"""<section class="assine" id="assine">
    <div>
      <h3>{titulo}</h3>
      <p>{texto}</p>
    </div>
    <div>
      <form class="form-linha" name="assinantes" method="POST" data-netlify="true" action="/obrigado/">
        <input type="hidden" name="form-name" value="assinantes">
        <input type="email" name="email" placeholder="seu@email.com.br" aria-label="Seu e-mail" required>
        <button class="botao botao-cheio" type="submit">Quero receber</button>
      </form>
      <p class="form-nota">Seu e-mail é usado só para enviar a carta, e você sai quando quiser.</p>
    </div>
  </section>"""


def rodape(rel):
    return f"""
<footer class="rodape-min">
  <div class="env">
    <div class="rodape-min-linha">
      <a class="marca-lockup compacta" href="{rel}">{MARCA}</a>
      <ul>
        <li><a href="{rel}tech/">Tech</a></li>
        <li><a href="{rel}bitcoin/">Bitcoin</a></li>
        <li><a href="{rel}historia/">História</a></li>
        <li><a href="{rel}economia/">Economia</a></li>
        <li><a href="{rel}ms/">MS</a></li>
        <li><a href="{rel}sobre/">Sobre</a></li>
        <li><a href="https://instagram.com/economistarenato" target="_blank" rel="noopener">Instagram</a></li>
      </ul>
    </div>
    <p class="rodape-min-fim">© {date.today().year} Renato W. Gomes · Economista, CORECON-MS 1297 · WGSA</p>
  </div>
</footer>
</body>
</html>
"""


def escreve(caminho, conteudo):
    p = os.path.join(SITE, caminho, "index.html") if not caminho.endswith(".html") else os.path.join(SITE, caminho)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(conteudo)
    print("ok", os.path.relpath(p, RAIZ))


def cartao_edicao(ed, rel):
    return f"""    <article class="cartao">
      <a href="{rel}arquivo/{ed['slug']}/">
        <span class="chapeu">Arquivo · {rotulo_num(ed)} · {e((serie_de(ed) or {}).get('curto', ''))} · {e(ed['data'])}</span>
        <h3 class="tit tit-g">{e(ed['titulo'])}</h3>
        <p class="olho">{e(ed['chamada'])}</p>
        <span class="selo">Leitura: {minutos(ed)} min</span>
      </a>
    </article>"""



# ------------------------------------------------------------------ séries da AEA (eixo do Arquivo · Estados Unidos)
SERIES_AEA = [
    {"slug": "publications", "nome": "Publications of the American Economic Association", "curto": "Publications", "periodo": "1886–1907",
     "pub": ["Publications of the American Economic Association"],
     "texto": "A série de monografias e anais com que a associação começou: um estudo por número, mais os relatórios das reuniões anuais."},
    {"slug": "economic-studies", "nome": "Economic Studies of the American Economic Association", "curto": "Economic Studies", "periodo": "1896–1899",
     "pub": ["Economic Studies"],
     "texto": "Série bimestral de estudos mais curtos, publicada ao lado das Publications entre 1896 e 1899. Numeração própria (ES 1, ES 2…)."},
    {"slug": "quarterly", "nome": "American Economic Association Quarterly", "curto": "Quarterly", "periodo": "1908–1910",
     "pub": ["American Economic Association Quarterly"],
     "texto": "Nova forma das Publications: monografias, anais das reuniões e o manual da associação, em quatro números por ano."},
    {"slug": "economic-bulletin", "nome": "The Economic Bulletin", "curto": "Economic Bulletin", "periodo": "1908–1910",
     "pub": ["The Economic Bulletin"],
     "texto": "Boletim trimestral de notas, resenhas de livros e bibliografia, que preparou o terreno para a revista."},
    {"slug": "american-economic-review", "nome": "The American Economic Review", "curto": "American Economic Review", "periodo": "1911–1929",
     "pub": ["The American Economic Review"],
     "texto": "A revista da associação desde 1911, que reuniu o Quarterly e o Bulletin: artigos, comunicações, resenhas e os anais das reuniões."},
]


def serie_de(ed):
    for s_ in SERIES_AEA:
        if ed.get("publicacao") in s_["pub"] or ed.get("serie") == s_["slug"]:
            return s_
    return None


def rotulo_num(ed):
    """'Nº 12' para a numeração geral; 'ES 3' para a Economic Studies (numeração própria)."""
    n = str(ed.get("numero", ""))
    return n if n.startswith("ES") else f"Nº {n}"


MESES = {"janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4, "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
         "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12}


def chave_data(ed):
    d = str(ed.get("data", "")).lower()
    mes = next((v for k, v in MESES.items() if k in d), 0)
    return (ano_edicao(ed), mes)


# ------------------------------------------------------------------ páginas
def pagina_inicio():
    """Capa: enigmática e mínima. Não é divulgada; o marketing vai direto para /tech, /historia e /economia."""
    rel = ""
    corpo = f"""
<main class="capa-enigma">
  <a class="capa-marca" href="./" aria-label="Renato W. Gomes, economista">{MARCA_TAG}</a>
  <p class="capa-frase">Cinco perguntas. Uma resposta por porta.</p>
  <nav class="capa-portas" aria-label="Interesses">
    <a href="tech/"><span>/tech</span><small>máquinas que trabalham</small></a>
    <a href="bitcoin/"><span>/bitcoin</span><small>dinheiro sem dono</small></a>
    <a href="historia/"><span>/historia</span><small>o que já aconteceu</small></a>
    <a href="economia/"><span>/economia</span><small>o que já foi escrito</small></a>
    <a href="ms/"><span>/ms</span><small>o chão onde se pisa</small></a>
  </nav>
  <p class="capa-rodape">Campo Grande · MS</p>
</main>
</body>
</html>
"""
    escreve("", cabeca("Renato W. Gomes, economista", "Renato W. Gomes, economista (CORECON-MS 1297). Tecnologia, bitcoin, história e economia.", "", rel) + corpo)


def edicoes_de(cid):
    return [ed for ed in DADOS["edicoes"] if ed.get("colecao", "eua") == cid]


def subnav_arquivo(rel_arquivo, ativo):
    """Sub-navegação por região, logo abaixo do menu, em todas as páginas do Arquivo."""
    itens = [("", "Todas")] + [(c["id"] + "/", c["regiao"]) for c in COLECOES]
    links = "".join(f'<a href="{rel_arquivo}{h}"{" class=\"ativo\"" if h == ativo else ""}>{e(n)}</a>' for h, n in itens)
    return f'  <nav class="subnav" aria-label="Regiões do Arquivo"><span class="subnav-rot">Arquivo</span>{links}</nav>\n'


def cartao_colecao(c, rel_arquivo):
    n = len(edicoes_de(c["id"]))
    selo = f"{n} edições" if c["status"] == "ativa" else "Em preparação"
    sub = f"{e(c['periodico'])} · {e(c['periodo'])}" if c["periodico"] else "Periódico em escolha"
    return f"""    <article class="cartao colecao colecao-{c['id']}">
      <a href="{rel_arquivo}{c['id']}/">
        <span class="chapeu">Coleção · {e(c['regiao'])}</span>
        <h3 class="tit tit-g">{e(c['titulo'])}</h3>
        <p class="olho">{e(c['descricao'])}</p>
        <span class="selo">{selo}</span>
        <span class="colecao-sub">{sub}</span>
      </a>
    </article>"""


def pagina_arquivo():
    rel = "../"
    cards = "\n".join(cartao_colecao(c, "") for c in COLECOES)
    eua = edicoes_de("eua")
    recentes = "\n".join(cartao_edicao(ed, rel) for ed in eua[-3:][::-1])
    corpo = f"""
<main class="env">
{subnav_arquivo("", "")}
  <div class="artigo-topo" style="max-width:820px;margin:28px auto 10px">
    <span class="chapeu">Arquivo · Clássicos comentados</span>
    <h1>Os debates que criaram a economia moderna</h1>
    <p class="olho">Um periódico de referência por região, lido no original e explicado em português — com o documento sempre a um clique e a pergunta de hoje no fim de cada texto.</p>
    <p class="olho" style="font-size:15px">Também no Arquivo: <a href="../ensaios/">Ensaios</a>, os textos longos, e <a href="../notas/">Notas · Então × Agora</a>.</p>
  </div>

  <div class="faixa">
    <h2>Coleções</h2>
    <span class="sub">Estados Unidos, China e Europa</span>
  </div>
  <section class="grade-3">
{cards}
  </section>

  <div class="faixa">
    <h2>Edições mais recentes</h2>
    <span class="sub">Estados Unidos</span>
    <a class="mais" href="eua/">Ver todas &rarr;</a>
  </div>
  <section class="grade-3">
{recentes}
  </section>

  <div class="faixa">
    <h2>Edições por ano</h2>
    <span class="sub">Estados Unidos, 1886–1929</span>
  </div>
{barra_anos(eua, "eua/")}

  {assine("Uma edição comentada por semana, no seu e-mail.", "O resumo em português, o documento original e a ponte com o debate de hoje.")}
</main>
"""
    escreve("arquivo", cabeca("Arquivo · Clássicos comentados — Economista Renato Gomes", "Os debates que criaram a economia moderna: um periódico de referência por região — Estados Unidos, China e Europa — lido no original e comentado em português.", "arquivo/", rel)
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))


def ano_edicao(ed):
    m = re.findall(r"(1[89]\d\d)", str(ed.get("data", "")))
    return int(m[-1]) if m else 0


def barra_anos(eds, base):
    """Barra de anos clicável, agrupada por década (base = prefixo do link até a página da coleção)."""
    anos = sorted({ano_edicao(ed) for ed in eds if ano_edicao(ed)})
    decadas = {}
    for a in anos: decadas.setdefault(a // 10 * 10, []).append(a)
    linhas = "\n".join(
        f'    <div class="anos-decada"><span class="anos-rotulo">{d}s</span>'
        + "".join(f'<a href="{base}#ano-{a}">{a}</a>' for a in lst) + "</div>"
        for d, lst in sorted(decadas.items()))
    return f'  <nav class="barra-anos" aria-label="Edições por ano">\n{linhas}\n  </nav>'


def secoes_por_ano(eds, rel):
    """Edições agrupadas por ano: título do ano, nº de edições e as séries publicadas naquele ano."""
    grupos = {}
    for ed in eds: grupos.setdefault(ano_edicao(ed), []).append(ed)
    out = []
    for a, lst in sorted(grupos.items()):
        lst = sorted(lst, key=chave_data)
        series = []
        for ed in lst:
            p = ed.get("publicacao", "")
            if p and p not in series: series.append(p)
        cards = "\n".join(cartao_edicao(ed, rel) for ed in lst)
        n = len(lst)
        out.append(f'''  <section class="ano-bloco" id="ano-{a}">
    <div class="ano-cab"><h3>{a}</h3><span class="sub">{n} {"edição" if n == 1 else "edições"} · {e(" · ".join(series))}</span></div>
    <div class="grade-3">
{cards}
    </div>
  </section>''')
    return "\n".join(out)


def bloco_series(eds, base):
    cards = []
    for s_ in SERIES_AEA:
        lst = [ed for ed in eds if serie_de(ed) is s_]
        n = len(lst)
        cont = f"{n} {'edição' if n == 1 else 'edições'}" if n else "em preparação"
        cards.append(f"""    <article class="cartao">
      <a href="{base}{s_['slug']}/">
        <span class="chapeu">{e(s_['periodo'])}</span>
        <h3 class="tit">{e(s_['nome'])}</h3>
        <p class="olho">{e(s_['texto'])}</p>
        <span class="selo">{cont}</span>
      </a>
    </article>""")
    return ('  <div class="faixa">\n    <h2>Por publicação</h2>\n    <span class="sub">As séries da American Economic Association</span>\n  </div>\n'
            '  <section class="grade-3">\n' + "\n".join(cards) + "\n  </section>")


def pagina_serie(c, s_):
    rel = "../../../"
    eds = [ed for ed in edicoes_de(c["id"]) if serie_de(ed) is s_]
    n = len(eds)
    lista = (barra_anos(eds, "") + "\n" + secoes_por_ano(eds, rel)) if eds else '  <p class="olho">Edições em preparação.</p>'
    corpo = f"""
<main class="env">
{subnav_arquivo("../../", c["id"] + "/")}
  <div class="artigo-topo" style="max-width:820px;margin:28px auto 10px">
    <span class="chapeu"><a href="../">Arquivo · Publicações da American Economic Association</a></span>
    <h1>{e(s_['nome'])} ({e(s_['periodo'])})</h1>
    <p class="olho">{e(s_['texto'])}</p>
  </div>
  <div class="faixa">
    <h2>{e(s_['curto'])}</h2>
    <span class="sub">{n} {'edição publicada' if n == 1 else 'edições publicadas'} · {e(s_['periodo'])}</span>
  </div>
{lista}
  <div class="corpo" style="max-width:820px;margin:0">
    <p class="nota-legal">Fonte: {e(c['fonte'])}. {e(c['licenca'])}</p>
  </div>
</main>
"""
    escreve(f"arquivo/{c['id']}/{s_['slug']}", cabeca(f"{s_['nome']} ({s_['periodo']}) — Arquivo · Economista Renato Gomes", s_["texto"], f"arquivo/{c['id']}/{s_['slug']}/", rel)
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))


def pagina_colecao(c):
    rel = "../../"
    eds = edicoes_de(c["id"])
    if c["status"] == "ativa" and eds:
        prox = "\n".join(f"          <li>{e(p)}</li>" for p in DADOS.get("proximas", [])) if c["id"] == "eua" else ""
        miolo = f"""  <div class="faixa">
    <h2>{e(c['periodico'])}</h2>
    <span class="sub">{len(eds)} edições publicadas · {e(c['periodo'])}</span>
  </div>
{bloco_series(eds, "")}
  <div class="faixa">
    <h2>Por ano</h2>
    <span class="sub">Todas as séries, em ordem cronológica</span>
  </div>
{barra_anos(eds, "")}
{secoes_por_ano(eds, rel)}
""" + (f"""
  <div class="faixa">
    <h2>Próximas edições</h2>
    <span class="sub">Na ordem de publicação</span>
  </div>
  <div class="corpo" style="max-width:820px;margin:0">
    <ul>
{prox}
    </ul>
  </div>
""" if prox else "")
        nota = f"Fonte: {e(c['fonte'])}. {e(c['licenca'])} Os resumos e comentários são do autor deste site." + (" Não são comentados, por não serem textos de economia, o suplemento com os estatutos da associação (1889) e os índices gerais das publicações (o de 1886 a 1896 e o suplemento de dezembro de 1917)." if c["id"] == "eua" else "")
    else:
        miolo = """  <section class="em-preparacao">
    <span class="selo">Em preparação</span>
    <h2>Esta coleção ainda não tem edições publicadas.</h2>
    <p>O periódico desta região está em escolha. Quando ele for definido, as edições entram aqui no mesmo formato do Arquivo: resumo em português, o documento original a um clique, glossário e a pergunta de hoje.</p>
    <p>Quer ser avisado da primeira edição? Assine a carta abaixo.</p>
  </section>
"""
        nota = "As fontes, o período e o regime de direitos autorais do periódico serão indicados aqui quando a coleção for aberta."
    corpo = f"""
<main class="env">
{subnav_arquivo("../", c["id"] + "/")}
  <div class="artigo-topo" style="max-width:820px;margin:28px auto 10px">
    <span class="chapeu">Arquivo · {e(c['regiao'])}</span>
    <h1>{e(c['titulo'])}</h1>
    <p class="olho">{e(c['descricao'])}</p>
  </div>
{miolo}
  <div class="corpo" style="max-width:820px;margin:0">
    <p class="nota-legal">{nota}</p>
  </div>
  {assine("Uma edição comentada por semana, no seu e-mail.", "O resumo em português, o documento original e a ponte com o debate de hoje.")}
</main>
"""
    escreve(f"arquivo/{c['id']}", cabeca(f"Arquivo · {c['regiao']} — Economista Renato Gomes", c["descricao"][:155], f"arquivo/{c['id']}/", rel)
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))



def barras_svg(b):
    """Gráfico de barras horizontais em SVG inline (bloco 'barras'): rotulos, series [{nome, valores}], unidade, legenda, fonte."""
    cores = ["#003097", "#03A9F4", "#9AA5B1", "#1A1A1A"]
    rot, ser = b["rotulos"], b["series"]
    un = b.get("unidade", "")
    vmax = max(max(s["valores"]) for s in ser) or 1
    W, LX, BW = 640, 195, 390
    bh, gap = 11, 9
    gh = len(ser) * bh + gap
    topo = 26 if len(ser) > 1 else 6
    H = topo + len(rot) * gh + 4
    fmt = lambda v: (f"{v:.1f}".replace(".", ",") if isinstance(v, float) else f"{v:,}".replace(",", ".")) + un
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{html.escape(b.get("legenda", ""), quote=True)}" '
           f'style="font-family:Inter,Arial,sans-serif;font-size:11px;max-width:{W}px;display:block;margin:0 auto">']
    if len(ser) > 1:
        x = LX
        for k, s in enumerate(ser):
            out.append(f'<rect x="{x}" y="6" width="10" height="10" fill="{cores[k % 4]}"/><text x="{x + 14}" y="15" fill="#1A1A1A">{html.escape(s["nome"])}</text>')
            x += 22 + 7 * len(s["nome"])
    for i, r in enumerate(rot):
        y0 = topo + i * gh
        out.append(f'<text x="{LX - 8}" y="{y0 + len(ser) * bh / 2 + 4}" text-anchor="end" fill="#1A1A1A">{html.escape(r)}</text>')
        for k, s in enumerate(ser):
            v = s["valores"][i]
            w = max(0.5, BW * v / vmax)
            y = y0 + k * bh
            out.append(f'<rect x="{LX}" y="{y}" width="{w:.1f}" height="{bh - 2}" fill="{cores[k % 4]}"/>'
                       f'<text x="{LX + w + 4:.1f}" y="{y + bh - 3}" fill="#444" font-size="9.5">{fmt(v)}</text>')
    out.append("</svg>")
    return "".join(out)


def render_blocos(blocos):
    """Corpo em blocos: p, h2 (pergunta), caixa (número-chave), citacao (tradução + original), leitura (análise do autor)."""
    out = []
    for b in blocos:
        t = b.get("tipo")
        if t == "p":
            out.append(f"    <p>{e(b['texto'])}</p>")
        elif t == "h2":
            ancora = f' id="art-{b["artigo"]}"' if b.get("artigo") else ""
            out.append(f"    <h2{ancora}>{e(b['texto'])}</h2>")
            if b.get("artigo") and b.get("credito"):
                out.append(f'    <p class="credito-art">{e(b["credito"])}</p>')
        elif t == "comentario":
            out.append(f'    <p class="ler-coment"><a href="{e(b["slug"])}/">{e(b.get("texto") or "Ler o comentário completo")} &rarr;</a></p>')
        elif t == "subtopico":
            ancora = "st-" + b["numero"].replace(".", "-")
            out.append(f'    <h2 class="subtopico" id="{ancora}"><span class="st-num">{e(b["numero"])}</span> {e(b["texto"])}</h2>')
        elif t == "h3":
            out.append(f'    <h3 class="pergunta">{e(b["texto"])}</h3>')
        elif t == "propostas":
            li = "".join(f"<li>{e(x)}</li>" for x in b["texto"])
            out.append(f'    <div class="caixa-como caixa-propostas">\n      <h3>{e(b["titulo"])}</h3>\n      <ol>{li}</ol>\n    </div>')
        elif t == "caixa":
            out.append(f'    <div class="caixa-num">\n      <div class="valor">{e(b["valor"])}</div>\n      <div class="exp">{e(b["texto"])}</div>\n    </div>')
        elif t == "citacao":
            orig = f' <span class="citacao-original">({e(b["original"])})</span>' if b.get("original") else ""
            out.append(f'    <div class="citacao">\n      <p>{e(b["texto"])}{orig}</p>\n    </div>')
        elif t == "tabela":
            cab = "".join(f"<th>{e(c)}</th>" for c in b["cabecalho"])
            lin = "\n".join("        <tr>" + "".join(f"<td>{e(str(c))}</td>" for c in l) + "</tr>" for l in b["linhas"])
            leg = f"<caption>{e(b['legenda'])}</caption>" if b.get("legenda") else ""
            out.append(f'    <div class="tabela-wrap"><table class="tabela-guia">{leg}\n      <thead><tr>{cab}</tr></thead>\n      <tbody>\n{lin}\n      </tbody>\n    </table></div>')
        elif t == "barras":
            leg = f"<figcaption>{e(b['legenda'])}</figcaption>" if b.get("legenda") else ""
            fonte = f'<p class="nota">{e(b["fonte"])}</p>' if b.get("fonte") else ""
            out.append(f'    <figure class="grafico-barras" style="margin:1.5em 0">{leg}{barras_svg(b)}{fonte}</figure>')
        elif t == "detalhes":
            out.append(f'    <details class="detalhes">\n      <summary>{e(b["titulo"])}</summary>\n{render_blocos(b["blocos"])}\n    </details>')
        elif t == "leitura":
            ps = "".join(f"<p>{e(x)}</p>" for x in b["texto"])
            out.append(f'    <div class="caixa-leitura leitura-autor">\n      <h3>Na minha leitura</h3>\n      {ps}\n    </div>')
    return "\n".join(out)


def minutos(item):
    """Tempo estimado de leitura: palavras do corpo (+ 'E hoje?' e glossário), 200 palavras/min, arredondado para cima."""
    import math
    if "blocos" in item:
        n = palavras(item["blocos"]) + len(item.get("hoje", "").split())
        n += sum(len(t.split()) + len(d.split()) for t, d in item.get("glossario", []))
    else:
        n = sum(len(t.split()) + len(x.split()) for t, x in item.get("pontos", [])) + len(item.get("hoje", "").split())
    return max(1, math.ceil(n / 200))


def palavras(blocos):
    n = 0
    for b in blocos:
        x = b.get("texto", "")
        n += sum(len(s.split()) for s in (x if isinstance(x, list) else [x]))
    return n


def glossario_html(g):
    if not g: return ""
    itens = "\n".join(f"        <dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in g)
    return f'    <div class="glossario">\n      <h3>Glossário</h3>\n      <dl>\n{itens}\n      </dl>\n    </div>'


def figura_html(slug, rel, legenda):
    img = os.path.join(SITE, "assets", "arquivo", f"{slug}.jpg")
    if not os.path.exists(img): return ""
    return (f'  <figure class="artigo-figura doc-original">\n    <img src="{rel}assets/arquivo/{slug}.jpg" alt="{e(legenda)}" loading="lazy">\n'
            f'    <figcaption>{e(legenda)} <span class="credito">Domínio público · JSTOR Early Journal Content / Internet Archive</span></figcaption>\n  </figure>')


def tipo_item_aer(titulo_original):
    """Classifica um item da AER pelo título do metadado (JSTOR)."""
    t = titulo_original or ""
    if t.startswith(("[untitled]", "Review: ")): return "resenha"
    if t.startswith("New Book"): return "livros"
    if re.search(r"Documents|Periodicals|^Notes|List of Doctoral|Communication|Personal and Miscellaneous|Back Matter|^Purposes of|^Constitution of|List of Members|^Program|Doctoral Dissertations|Geographical Index|^Book Reviews|^Review: |^Volume Information|^Front Matter|^Book Notes|^Foreword|^A List of|^Preface|^Correspondence|^Index of|^Books Reviewed|^Publications of the American Economic|^\[[^\]]*\]$|^\[.*\]: ", t): return "docs"
    return "artigo"


def item_artigo_html(ed, a, rel):
    link = (f' · <a href="{rel}arquivo/{ed["slug"]}/{a["ensaio_slug"]}/">ler o comentário</a>' if a.get("ensaio_slug") else "")
    return (f'        <li><b>{e(a["titulo"])}</b>' + (f' — {e(a["autores"])}' if a.get("autores") else "")
            + (f' ({e(a["paginas"])})' if a.get("paginas") else "") + (f'. {e(a["resumo"])}' if a.get("resumo") else "")
            + (f' <a href="https://www.jstor.org/stable/{a["jstor"]}" target="_blank" rel="noopener">JSTOR</a>' if a.get("jstor") and not str(a["jstor"]).startswith("ia-") else "")
            + link + "</li>")


def artigos_em_blocos(ed, rel, arts):
    """AER: artigos em destaque, depois resenhas, novos livros e documentos/periódicos/notas."""
    orig = {i[2]: i[0] for i in ed.get("itens", [])}
    grupos = {"artigo": [], "resenha": [], "livros": [], "docs": []}
    for a in arts:
        grupos[tipo_item_aer(orig.get(a.get("jstor"), a.get("titulo", "")))].append(a)
    nomes = [("artigo", "Artigos"), ("resenha", "Resenhas"), ("livros", "Novos livros"), ("docs", "Documentos, periódicos e notas")]
    out = []
    for k, nome in nomes:
        g = grupos[k]
        if not g: continue
        secoes = {b.get("artigo") for b in ed.get("blocos", []) if b.get("artigo")}
        if k == "artigo" and secoes:
            lis = []
            for a in g:
                ln = f'        <li><b>{e(a["titulo"])}</b>' + (f' — {e(a["autores"])}' if a.get("autores") else "") + (f' ({e(a["paginas"])})' if a.get("paginas") else "")
                if a.get("jstor") in secoes: ln += f' · <a href="#art-{a["jstor"]}">resenha acima</a>'
                elif a.get("resumo"): ln += f'. {e(a["resumo"])}'
                if a.get("ensaio_slug"): ln += f' · <a href="{rel}arquivo/{ed["slug"]}/{a["ensaio_slug"]}/">comentário completo</a>'
                if a.get("jstor") and not str(a["jstor"]).startswith("ia-"): ln += f' · <a href="https://www.jstor.org/stable/{a["jstor"]}" target="_blank" rel="noopener">JSTOR</a>'
                lis.append(ln + "</li>")
            out.append(f'      <h3>{nome} ({len(g)})</h3>\n      <ol class="artigos-principais">\n' + "\n".join(lis) + "\n      </ol>")
            continue
        cls = ' class="artigos-principais"' if k == "artigo" else ""
        out.append(f'      <h3>{nome} ({len(g)})</h3>\n      <ol{cls}>\n' + "\n".join(item_artigo_html(ed, a, rel) for a in g) + "\n      </ol>")
    return '    <div class="artigos-edicao">\n' + "\n".join(out) + "\n    </div>\n"


def artigos_html(ed, rel):
    """Modelo híbrido (AER): a edição lista seus artigos; um artigo pode ter página comentada própria
    (campo 'ensaio_slug' -> /arquivo/<edicao>/<artigo>/). Sem 'artigos', nada é exibido."""
    arts = ed.get("artigos") or []
    if not arts: return ""
    if ed.get("publicacao") == "The American Economic Review":
        return artigos_em_blocos(ed, rel, arts)
    linhas = []
    for a in arts:
        link = (f' · <a href="{rel}arquivo/{ed["slug"]}/{a["ensaio_slug"]}/">ler o comentário</a>' if a.get("ensaio_slug") else "")
        linhas.append(f'        <li><b>{e(a["titulo"])}</b>' + (f' — {e(a["autores"])}' if a.get("autores") else "")
                      + (f' ({e(a["paginas"])})' if a.get("paginas") else "") + (f'. {e(a["resumo"])}' if a.get("resumo") else "")
                      + (f' <a href="https://www.jstor.org/stable/{a["jstor"]}" target="_blank" rel="noopener">JSTOR</a>' if a.get("jstor") and not str(a["jstor"]).startswith("ia-") else "")
                      + link + "</li>")
    return '    <div class="artigos-edicao">\n      <h3>Artigos desta edição</h3>\n      <ol>\n' + "\n".join(linhas) + "\n      </ol>\n    </div>\n"


def pagina_edicao(ed, anterior, proxima):
    rel = "../../"
    if "blocos" in ed:
        mins = max(3, round(palavras(ed["blocos"]) / 200))
        miolo = render_blocos(ed["blocos"]) + "\n" + glossario_html(ed.get("glossario"))
        hoje = ed.get("hoje", "")
        fig = figura_html(ed["slug"], rel, f"Página original: {ed['publicacao']}, {ed['volume']} ({ed['data']}).")
        corpo_ed = f"""  <div class="corpo">
{miolo}

    <div class="caixa-num">
      <div class="valor">E hoje?</div>
      <div class="exp">{e(hoje)}</div>
    </div>
"""
        return pagina_edicao_html(ed, anterior, proxima, rel, corpo_ed, fig, "")
    pontos = "\n".join(f"      <li><b>{e(t)}.</b> {e(x)}</li>" for t, x in ed["pontos"])
    corpo_ed = f"""  <div class="corpo">
    <h2>O que diz o documento</h2>
    <ol>
{pontos}
    </ol>

    <div class="caixa-num">
      <div class="valor">E hoje?</div>
      <div class="exp">{e(ed['hoje'])}</div>
    </div>
"""
    return pagina_edicao_html(ed, anterior, proxima, rel, corpo_ed, "", "")


def links_original(ed, j):
    """Links para o original: JSTOR (id numérico) e Internet Archive (item jstor-<id> até 1922;
    número completo 'sim_' de 1923 em diante, campo 'archive_id' da edição). Ids 'ia-...' são internos."""
    j = str(j or "")
    ia = ed.get("archive_id")
    out = []
    if j and not j.startswith("ia-"):
        out.append(f'<a href="https://www.jstor.org/stable/{j}" target="_blank" rel="noopener">JSTOR</a>')
    if ia:
        out.append(f'<a href="https://archive.org/details/{ia}" target="_blank" rel="noopener">Internet Archive (número completo, PDF)</a>')
    elif j and not j.startswith("ia-"):
        out.append(f'<a href="https://archive.org/details/jstor-{j}" target="_blank" rel="noopener">Internet Archive (PDF)</a>')
    return " · ".join(out)


def linha_sumario(ed):
    partes = []
    if ed.get("jstor_edicao"):
        partes.append(f'        <li>Sumário da edição no JSTOR: <a href="https://www.jstor.org/stable/10.2307/{ed["jstor_edicao"]}" target="_blank" rel="noopener">{e(ed["publicacao"])}, {e(ed["volume"])}</a>.</li>')
    if ed.get("archive_id"):
        partes.append(f'        <li>Número completo digitalizado (domínio público): <a href="https://archive.org/details/{ed["archive_id"]}" target="_blank" rel="noopener">Internet Archive</a>.</li>')
    return "\n".join(partes)


def pagina_edicao_html(ed, anterior, proxima, rel, corpo_ed, fig, leitura_min):
    itens = "\n".join(f'        <li><b>{e(t)}</b>' + (f' ({e(p)})' if p else '') + '. ' + links_original(ed, j) + '</li>' for t, p, j in ed["itens"])
    nav = []
    if anterior: nav.append(f'<a href="../{anterior["slug"]}/">&larr; {rotulo_num(anterior)} · {e(anterior["titulo"])}</a>')
    if proxima: nav.append(f'<a href="../{proxima["slug"]}/">{rotulo_num(proxima)} · {e(proxima["titulo"])} &rarr;</a>')
    corpo = f"""
<div class="env">
{subnav_arquivo("../", ed.get("colecao", "eua") + "/")}</div>
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu">Arquivo · {rotulo_num(ed)} · {e(ed['publicacao'])}, {e(ed['volume'])} ({e(ed['data'])})</span>
    <h1>{e(ed['titulo'])}</h1>
    <p class="tempo-leitura">Leitura: {minutos(ed)} min</p>
    <p class="olho">{e(ed['chamada'])}</p>
    <div class="barra-autor">
      <div class="mini"><img src="{rel}assets/monograma-branco.png" alt=""></div>
      <div class="quem">
        <b>Comentado por Renato W. Gomes</b>
        <span>Original: “{e(ed['titulo_original'])}” — {e(ed['autores'])}{leitura_min}</span>
      </div>
    </div>
  </div>
{fig}
{corpo_ed}
{artigos_html(ed, rel)}
    <div class="fontes">
      <h3>Fontes</h3>
      <ol>
{itens}
{linha_sumario(ed)}
      </ol>
    </div>

    <p class="nota-legal">Documento em domínio público (EUA, publicado antes de 1931), via JSTOR Early Journal Content e Internet Archive. Resumo e comentário do autor deste site, sem afiliação com a American Economic Association. Encontrou um erro? Escreva: a correção é publicada no próprio texto, com data.</p>

    <p class="fonte-links" style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">{' '.join(nav)}</p>
  </div>
</article>

<div class="env">
  {assine("Uma edição comentada por semana, no seu e-mail.", "O resumo em português, o documento original e a ponte com o debate de hoje.")}
</div>
"""
    escreve(f"arquivo/{ed['slug']}", cabeca(f"{ed['titulo']} — Arquivo · Economista Renato Gomes", ed["chamada"], f"arquivo/{ed['slug']}/", rel, "article")
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))


def pagina_comentario(ed, c, anterior=None, proxima=None):
    """Modelo híbrido: artigo comentado dentro de uma edição (campo 'comentarios' da edição)."""
    rel = "../../../"
    nav = [f'<a href="../">&uarr; {rotulo_num(ed)} · {e(ed["titulo"])}</a>']
    if anterior: nav.insert(0, f'<a href="../{anterior["slug"]}/">&larr; {e(anterior["titulo"])}</a>')
    if proxima: nav.append(f'<a href="../{proxima["slug"]}/">{e(proxima["titulo"])} &rarr;</a>')
    fig = figura_html(f'{ed["slug"]}--{c["slug"]}', rel, f"Página original: {c['titulo_original']}, {ed['publicacao']}, {ed['volume']} ({ed['data']}).")
    j = c.get("jstor", "")
    fonte = (f'        <li><b>{e(c["titulo_original"])}</b> — {e(c["autores"])} ({e(c["paginas"])}). '
             + links_original(ed, j) + '</li>')
    corpo = f"""
<div class="env">
{subnav_arquivo("../../", ed.get("colecao", "eua") + "/")}</div>
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu"><a href="../">Arquivo · {rotulo_num(ed)} · {e(ed['publicacao'])}, {e(ed['volume'])} ({e(ed['data'])})</a></span>
    <h1>{e(c['titulo'])}</h1>
    <p class="tempo-leitura">Leitura: {minutos(c)} min</p>
    <p class="olho">{e(c['chamada'])}</p>
    <div class="barra-autor">
      <div class="mini"><img src="{rel}assets/monograma-branco.png" alt=""></div>
      <div class="quem">
        <b>Comentado por Renato W. Gomes</b>
        <span>Original: “{e(c['titulo_original'])}” — {e(c['autores'])}, {e(c['paginas'])}</span>
      </div>
    </div>
  </div>
{fig}
  <div class="corpo">
{render_blocos(c['blocos'])}
{glossario_html(c.get('glossario'))}

    <div class="caixa-num">
      <div class="valor">E hoje?</div>
      <div class="exp">{e(c.get('hoje', ''))}</div>
    </div>

    <div class="fontes">
      <h3>Fontes</h3>
      <ol>
{fonte}
        <li>Edição completa, com os demais artigos: <a href="../">{rotulo_num(ed)} do Arquivo</a>.</li>
      </ol>
    </div>

    <p class="nota-legal">Documento em domínio público (EUA, publicado antes de 1931), via JSTOR Early Journal Content e Internet Archive. Resumo e comentário do autor deste site, sem afiliação com a American Economic Association. Encontrou um erro? Escreva: a correção é publicada no próprio texto, com data.</p>

    <p class="fonte-links" style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">{' '.join(nav)}</p>
  </div>
</article>
"""
    escreve(f"arquivo/{ed['slug']}/{c['slug']}", cabeca(f"{c['titulo']} — Arquivo · Economista Renato Gomes", c["chamada"], f"arquivo/{ed['slug']}/{c['slug']}/", rel, "article")
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))


NOTAS_ARQ = os.path.join(RAIZ, "scripts", "arquivo", "notas.json")
NOTAS = json.load(open(NOTAS_ARQ, encoding="utf-8"))["notas"] if os.path.exists(NOTAS_ARQ) else []


def cartao_nota(n, rel):
    return f"""    <article class="cartao">
      <a href="{rel}notas/{n['slug']}/">
        <span class="chapeu dado">Então × Agora</span>
        <h3 class="tit tit-g">{e(n['titulo'])}</h3>
        <p class="olho">{e(n['chamada'])}</p>
        <span class="selo">Leitura: {minutos(n)} min</span>
      </a>
    </article>"""


def pagina_notas():
    rel = "../"
    cartoes = "\n".join(cartao_nota(n, rel) for n in NOTAS)
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:40px auto 10px">
    <span class="chapeu dado">Notas · Então × Agora</span>
    <h1>Um número de ontem, um número de hoje</h1>
    <p class="olho">Notas curtas: um dado dos documentos de 1886–1929 ao lado de um dado atual, com as duas fontes. Para ler em três minutos.</p>
  </div>
  <section class="grade-3">
{cartoes}
  </section>
  {assine()}
</main>
"""
    escreve("notas", cabeca("Notas · Então × Agora — Economista Renato Gomes", "Um dado histórico ao lado de um dado atual, com as duas fontes.", "notas/", rel)
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))


def pagina_nota(n):
    rel = "../../"
    fontes = "\n".join(f'        <li>{e(d)}' + (f' — <a href="{e(u)}" target="_blank" rel="noopener">link</a>' if u else "") + "</li>" for d, u in n.get("fontes", []))
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu dado">Notas · Então × Agora</span>
    <h1>{e(n['titulo'])}</h1>
    <p class="tempo-leitura">Leitura: {minutos(n)} min</p>
    <p class="olho">{e(n['chamada'])}</p>
    <div class="barra-autor">
      <div class="mini"><img src="{rel}assets/monograma-branco.png" alt=""></div>
      <div class="quem"><b>Renato W. Gomes</b><span>Economista · CORECON-MS 1297</span></div>
    </div>
  </div>
  <div class="corpo">
    <div class="entao-agora">
      <div><span class="rot">Então</span><div class="num">{e(n['entao']['valor'])}</div><p>{e(n['entao']['texto'])}</p><small>{e(n['entao']['fonte'])}</small></div>
      <div><span class="rot">Agora</span><div class="num">{e(n['agora']['valor'])}</div><p>{e(n['agora']['texto'])}</p><small>{e(n['agora']['fonte'])}</small></div>
    </div>
{render_blocos(n['blocos'])}
    <div class="fontes">
      <h3>Fontes</h3>
      <ol>
{fontes}
      </ol>
    </div>
    <p class="nota-legal">Nota de análise do autor. Encontrou um erro? Escreva: a correção é publicada no próprio texto, com data.</p>
  </div>
</article>
<div class="env">
  {assine()}
</div>
"""
    escreve(f"notas/{n['slug']}", cabeca(f"{n['titulo']} — Notas · Economista Renato Gomes", n["chamada"], f"notas/{n['slug']}/", rel, "article")
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))


def cartao_comentario(ed, c, rel):
    """Artigo comentado da AER (modelo híbrido) listado em /ensaios/."""
    return f"""    <article class="cartao">
      <a href="{rel}arquivo/{ed['slug']}/{c['slug']}/">
        <span class="chapeu">Arquivo · Nº {ed['numero']} · {e(ed['data'])}</span>
        <h3 class="tit tit-g">{e(c['titulo'])}</h3>
        <p class="olho">{e(c['chamada'])}</p>
        <span class="selo">Leitura: {minutos(c)} min</span>
      </a>
    </article>"""


def ensaios():
    return [ed for ed in DADOS["edicoes"] if ed.get("ensaio")]


def pagina_ensaios():
    rel = "../"
    cards = []
    for ed in DADOS["edicoes"]:
        if ed.get("ensaio"): cards.append(cartao_edicao(ed, rel))
        for c in ed.get("comentarios", []):
            if c.get("ensaio") or palavras(c["blocos"]) >= 1100:
                cards.append(cartao_comentario(ed, c, rel))
    lista = "\n".join(cards)
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:40px auto 10px">
    <span class="chapeu opiniao">Ensaios</span>
    <h1>Ensaios</h1>
    <p class="olho">Os textos longos da casa: uma edição ou um tema lido a fundo, com a cena, os números, as citações traduzidas e a análise do autor. Para ler com calma.</p>
  </div>
  <section class="grade-3">
{lista}
  </section>
  {assine()}
</main>
"""
    escreve("ensaios", cabeca("Ensaios — Economista Renato Gomes", "Os textos longos da casa: clássicos e temas lidos a fundo, com fonte primária e análise do autor.", "ensaios/", rel)
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))


def pagina_analises():
    rel = "../"
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:40px auto 10px">
    <span class="chapeu dado">Análises</span>
    <h1>Contas públicas com fonte</h1>
    <p class="olho">Orçamento, arrecadação, renúncia fiscal, dívida e investimento no Brasil — da União aos estados e municípios — e comparações internacionais, lidos no documento oficial (LOA, LDO, Diário Oficial, SICONFI/RREO, Tesouro Nacional, IBGE, FMI, OCDE) e explicados em linguagem de gente.</p>
  </div>
  <div class="corpo" style="max-width:820px;margin:0 auto">
    <p><b>Em preparação.</b> As primeiras análises entram aqui em breve. Cada texto vai trazer, no rodapé, o documento de origem de cada número — e, quando couber, a planilha usada para quem quiser conferir.</p>
    <p>Enquanto isso, o <a href="../arquivo/">Arquivo</a> mostra de onde vêm muitas das perguntas de hoje: monopólios, concessões, tarifas e o papel do Estado já eram discutidos, com dados, em 1886.</p>
  </div>
  {assine("Seja avisado da primeira análise.", "Uma mensagem por semana, com a fonte oficial sempre no rodapé.")}
</main>
"""
    escreve("analises", cabeca("Análises — Economista Renato Gomes", "Contas públicas lidas no documento oficial e explicadas em linguagem de gente. Em preparação.", "analises/", rel)
            + topo("analises/", rel, completo=False) + corpo + rodape(rel))


def bloco_contato(assunto="Contato pelo site (/tech)", convite="Conte em poucas linhas qual tarefa toma mais tempo do seu time. Eu respondo em até dois dias úteis.", pergunta="Qual tarefa toma mais tempo do seu time hoje?", voltar="tech/", titulo="Fale comigo"):
    if FORM_CONTATO:
        form = f"""<form class="form-contato" action="{FORM_CONTATO}" method="POST">
        <input type="hidden" name="_subject" value="{assunto}">
        <input type="hidden" name="_next" value="{DOMINIO}/obrigado/?de={voltar}">
        <input type="hidden" name="_template" value="table">
        <input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off">
        <input type="text" name="nome" placeholder="Seu nome" aria-label="Seu nome" required>
        <input type="email" name="email" placeholder="seu@email.com.br" aria-label="Seu e-mail" required>
        <input type="text" name="empresa" placeholder="Empresa e área" aria-label="Empresa e área">
        <textarea name="mensagem" rows="4" placeholder="{pergunta}" aria-label="Mensagem" required></textarea>
        <button class="botao botao-cheio" type="submit">Enviar</button>
      </form>"""
    else:
        form = '<p class="aviso-preencher">[Formulário de contato: falta o endereço do Formspree e o e-mail de destino.]</p>'
    email = f' Ou escreva para <a href="mailto:{EMAIL_CONTATO}">{EMAIL_CONTATO}</a>.' if EMAIL_CONTATO else ""
    return f"""<section class="contato-min" id="contato">
    <div>
      <h2>{titulo}</h2>
      <p>{convite}{email}</p>
    </div>
    <div>
      {form}
    </div>
  </section>"""


def redireciona(caminho, destino):
    """Endereço antigo que passou a morar em outra página."""
    escreve(caminho, f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>Mudou de endereço</title>
<link rel="canonical" href="{DOMINIO}/{destino}"><meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=/{destino}"></head>
<body><p>Esta página mudou para <a href="/{destino}">{DOMINIO}/{destino}</a>.</p></body></html>
""")


def pagina_tech():
    rel = "../"
    corpo = f"""
<main class="env pagina-min">
  <section class="heroi heroi-interno">
    <p class="heroi-quem">Tech · Renato W. Gomes, economista</p>
    <h1>{FRASE}.</h1>
    <p class="heroi-olho">Encontro onde o seu time perde horas em tarefas repetitivas, coloco agentes de IA para fazer esse trabalho e meço o ganho em reais, mês a mês.</p>
    <p class="heroi-acoes"><a class="botao botao-cheio" href="#contato">Fale comigo</a> <a class="botao" href="#como">Como funciona</a></p>
  </section>

  <ol class="passos" id="como">
    <li>
      <span class="passo-num">1</span>
      <h2>Diagnóstico</h2>
      <p>Mapeio as tarefas repetitivas, quantas horas cada uma consome e quanto custa. Você recebe a conta do que vale automatizar e do que não vale.</p>
    </li>
    <li>
      <span class="passo-num">2</span>
      <h2>Implantação</h2>
      <p>Coloco agentes de IA nas tarefas escolhidas, como atendimento, conferência de documentos, conciliação e relatórios, ligados às ferramentas que a empresa já usa.</p>
    </li>
    <li>
      <span class="passo-num">3</span>
      <h2>Acompanhamento mensal</h2>
      <p>Ajusto os agentes, controlo a qualidade do que eles entregam e mando todo mês o relatório do ganho em horas e em reais.</p>
    </li>
  </ol>

  <section class="para-quem">
    <h2>Para quem</h2>
    <p>Escritórios de contabilidade, gestoras e assessorias de investimento, e empresas de serviços e do agro em Mato Grosso do Sul e Mato Grosso. Também faço palestras sobre IA e produtividade para quem decide.</p>
  </section>

  <section class="para-quem">
    <h2>Por que um economista</h2>
    <p>Muitas das perguntas que as empresas fazem hoje sobre IA já foram feitas quando as centrais telefônicas e as fábricas se automatizaram. A matemática criada para dimensionar telefonistas serve para dimensionar agentes; os métodos de controle de qualidade da indústria servem para conferir o que um agente entrega. Eu uso essa história como método, e a conta em reais como prova.</p>
  </section>

  {bloco_contato()}
</main>
"""
    escreve("tech", cabeca(f"Tech — {FRASE} · Renato W. Gomes", "Diagnóstico, implantação e acompanhamento de agentes de IA para pequenas e médias empresas, com o ganho medido em reais.", "tech/", rel)
            + topo("tech/", rel) + corpo + rodape(rel))


def conceitos_btc_html():
    if not CONCEITOS_BTC:
        return ""
    itens = "\n".join(f'    <h3 class="conceito-tit">{e(t)}</h3>\n' + "\n".join(f"    <p>{p_}</p>" for p_ in ps) for t, ps in CONCEITOS_BTC)
    return f"""  <section class="para-quem" id="conceitos">
    <h2>Conceitos</h2>
{itens}
  </section>
"""


def autores_btc_html(rel):
    if not AUTORES_BTC:
        return ""
    def nome(n, u):
        return f'<a href="{u}" target="_blank" rel="noopener">{e(n)}</a>' if u else e(n)
    li = "\n".join(f'      <li><b>{nome(n, u)}.</b> {e(t)}</li>' for n, t, u in AUTORES_BTC)
    obras = "\n".join(f'      <li><a href="{u}" target="_blank" rel="noopener"><i>{e(t)}</i></a> ({a}), {e(au)}. <span class="nota-min">{h}</span></li>' for au, t, a, u, h in OBRAS_BTC)
    return f"""  <section class="para-quem" id="autores">
    <h2>Quem me inspira</h2>
    <p>Esta é uma plataforma aberta: as regras, os testes e as referências ficam à vista. Estes são os sete autores de onde vêm as ideias testadas aqui, em ordem cronológica.</p>
    <ul class="lista-min">
{li}
    </ul>
    <h2 style="margin-top:28px">Leia no original</h2>
    <p>Os textos fundadores, de Dow e Wyckoff, estão em domínio público. Os demais autores têm direitos autorais em vigor; os livros estão à venda.</p>
    <ul class="lista-min">
{obras}
    </ul>
  </section>
"""


# Obras dos autores em domínio público (conferidas em 24/11/2026): (autor, título, ano, link, host)
OBRAS_BTC = [
    ("S. A. Nelson, com os editoriais de Charles Dow", "The ABC of Stock Speculation", "1903", "https://catalog.hathitrust.org/Record/001740713", "HathiTrust"),
    ("William Peter Hamilton, sucessor de Dow no Wall Street Journal", "The Stock Market Barometer", "1922", "https://babel.hathitrust.org/cgi/pt?id=uc2.ark:/13960/t42r3r118", "HathiTrust"),
    ("Richard D. Wyckoff", "How I Trade and Invest in Stocks and Bonds", "1922", "https://archive.org/details/cu31924031269552", "Internet Archive"),
]


# Conceitos explicados na /bitcoin: (título, texto em parágrafos). Um conceito novo = um item aqui.
CONCEITOS_BTC = [
    ("Faixas de percentis: onde o preço está dentro da sua própria história",
     ["Pegue os preços de fechamento das últimas 52 semanas e ordene do menor para o maior. O percentil diz em que ponto dessa fila o preço de hoje está: no percentil 10, só 10% das semanas fecharam mais baixo; no 90, só 10% fecharam mais alto.",
      "As faixas viram limites de força. Abaixo do percentil 20 fica o <b>limite inferior</b>: o preço está barato em relação ao próprio passado, e é ali que costuma aparecer a força compradora. Acima do percentil 80 fica o <b>limite superior</b>: o preço está caro, e é ali que a força vendedora costuma agir. Entre os dois, a faixa do meio é terreno neutro.",
      "Somando o volume negociado em cada faixa de preço, dá para ver onde mais gente comprou e vendeu. Esses níveis de preço com muito volume funcionam como memória do mercado: quem comprou ali tende a defender o preço na volta, e quem ficou preso ali tende a vender quando empata.",
      "No piloto, o conceito vira um sinal testável: comprar quando o fechamento semanal volta para cima do limite inferior e reduzir a posição quando perde força acima do limite superior."]),
    ("Os três movimentos e a tendência primária (Dow)",
     ["“O mercado deve sempre ser considerado como tendo três movimentos, todos acontecendo ao mesmo tempo” (“The market is always to be considered as having three movements, all going on at the same time”), escreveu Charles Dow em 1900, citado por William Peter Hamilton em <i>The Stock Market Barometer</i> (1922, cap. IV, p. 30). Há a oscilação diária, sem importância; a reação secundária, que dura semanas; e o movimento primário, que dura anos.",
      "A regra para saber em que maré se está é simples: “é um período de alta enquanto um topo supera os topos anteriores” (“It is a bull period as long as the average of one high point exceeds that of previous high points”) e de baixa quando o fundo fica abaixo dos fundos anteriores (p. 32). Dow também observou que um movimento primário costuma ter uma reação contrária de pelo menos três oitavos do seu tamanho (p. 37): é a correção que assusta, mas não muda a maré.",
      "O próprio Dow avisou dos limites: quem tenta operar só com essa teoria “encontra muitas exceções” (“find a good many exceptions”, p. 36). Por isso, aqui ela vira um sinal entre vários, testado contra os outros."]),
    ("Acumulação, alta e distribuição (Wyckoff)",
     ["Richard Wyckoff, em <i>How I Trade and Invest in Stocks and Bonds</i> (1922), descreve as campanhas dos grandes operadores em três etapas: acumulação, alta e distribuição (cap. II, p. 38-39). Na acumulação, quem sabe mais compra em silêncio, numa faixa de preço que pode durar semanas ou meses; na distribuição, vende para quem chega tarde.",
      "Duas regras dele viram filtros no piloto. A primeira: operar a favor da tendência multiplica as chances de acerto “três ou quatro vezes” (cap. II, p. 48). A segunda: o lucro esperado deve ser “pelo menos três ou quatro vezes” o tamanho do risco (“at least three or four times the amount of the risk”, cap. II, p. 49). E o dinheiro de verdade, dizia, estava nos movimentos de 30 a 60 dias, não no vaivém do dia."]),
]


# Autores que inspiram o piloto de bitcoin: (nome, o que ele ensina, link opcional). Lista vazia = seção some.
AUTORES_BTC = [
    ("Charles Dow", "Nos editoriais do Wall Street Journal, jornal que ele fundou, nasceu a ideia de que o mercado anda em tendências e de que elas se confirmam. É a raiz da média de 200 dias.", ""),
    ("Richard Wyckoff", "Ensinou a ler preço e volume juntos e a reconhecer as fases de acumulação e distribuição, quando quem sabe mais está comprando ou vendendo.", ""),
    ("Ralph Nelson Elliott", "Em The Wave Principle (1938), propôs que o mercado se move em ondas repetidas, movidas pela psicologia coletiva.", ""),
    ("Robert D. Edwards e John Magee", "Technical Analysis of Stock Trends (1948) catalogou os padrões gráficos, como ombro-cabeça-ombro, triângulos e suportes, e virou a bíblia dos grafistas.", ""),
    ("Richard Donchian", "Pioneiro dos sistemas de tendência com regras fixas: entrar no rompimento da máxima e sair na perda da mínima. É a base do sinal de rompimento testado aqui.", ""),
    ("J. Welles Wilder Jr.", "Em New Concepts in Technical Trading Systems (1978), criou o IFR, o ATR e o ADX, indicadores usados até hoje.", ""),
    ("Gerald Appel", "Criou o MACD no fim dos anos 1970, o indicador de momento mais popular dos gráficos.", ""),
]


# Diário do piloto: scripts/bitcoin/diario.csv (data AAAA-MM-DD, retorno_pct do dia, nota opcional).
# Só percentuais: o valor da carteira em reais nunca entra no site.
def diario_btc():
    import csv
    arq = os.path.join(RAIZ, "scripts", "bitcoin", "diario.csv")
    if not os.path.exists(arq):
        return []
    with open(arq, encoding="utf-8") as f:
        return [(r["data"], float(r["retorno_pct"].replace(",", ".")), r.get("nota", "")) for r in csv.DictReader(f) if r.get("data")]


def diario_btc_html():
    linhas = diario_btc()
    if not linhas:
        return """  <section class="para-quem" id="diario">
    <h2>Meu diário de retornos</h2>
    <p>Aqui eu publico, dia a dia, o retorno de uma posição de referência de 1 bitcoin, em percentual, com acertos e erros à vista. O diário começa no primeiro dia do piloto.</p>
  </section>
"""
    idx, acum = [], 100.0
    for _, r, _ in linhas:
        acum *= 1 + r / 100
        idx.append(acum)
    w, h, pad = 640, 180, 8
    lo, hi = min(idx + [100.0]), max(idx + [100.0])
    esc = (hi - lo) or 1
    n = max(len(idx) - 1, 1)
    pts = " ".join(f"{pad + i * (w - 2 * pad) / n:.1f},{h - pad - (v - lo) * (h - 2 * pad) / esc:.1f}" for i, v in enumerate(idx))
    y100 = h - pad - (100 - lo) * (h - 2 * pad) / esc
    total = idx[-1] - 100
    ult = linhas[::-1][:30]
    def pct(x):
        return f"{x:+.2f}%".replace(".", ",")
    tab = "\n".join(f'        <tr><td>{d[8:10]}/{d[5:7]}/{d[:4]}</td><td class="{"sobe" if r >= 0 else "desce"}">{pct(r)}</td><td>{e(nt)}</td></tr>' for d, r, nt in ult)
    return f"""  <section class="para-quem" id="diario">
    <h2>Meu diário de retornos</h2>
    <p>O retorno de uma posição de referência de 1 bitcoin, dia a dia, em percentual. Desde o início do piloto: <b>{pct(total)}</b> em {len(linhas)} dias.</p>
    <svg class="diario-graf" viewBox="0 0 {w} {h}" role="img" aria-label="Retorno acumulado, base 100">
      <line x1="{pad}" x2="{w - pad}" y1="{y100:.1f}" y2="{y100:.1f}" class="base"/>
      <polyline points="{pts}" class="linha"/>
    </svg>
    <table class="diario-tab">
      <thead><tr><th>Dia</th><th>Retorno</th><th>Nota</th></tr></thead>
      <tbody>
{tab}
      </tbody>
    </table>
  </section>
"""


CORES_BTC = {"Comprar e segurar": "#1A1A1A", "Cruzamento 10 x 40 semanas": "#003097", "Média de 40 semanas": "#03A9F4",
             "MACD semanal": "#7a5cff", "Rompimento 20 semanas": "#0a7d35", "Topos e fundos (Dow)": "#c77700",
             "Faixas de percentis 52 semanas": "#b0418f", "IFR semanal (30/70)": "#A61E1E", "Só CDI": "#9a9a9a"}
CORES_CONSENSO = {"Consenso 7 x 0": "#e4572e", "Consenso 6 x 1": "#d98e04", "Consenso 5 x 2": "#2a9d8f", "Consenso 4 x 3": "#5c4d7d"}


def cor_btc(nome):
    return CORES_CONSENSO.get(nome) or CORES_BTC.get(nome, "#666")


def data_br(iso):
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


MESES_ABR = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def decisao_btc(r):
    """Mesma regra da coluna "Decisão de domingo" da tabela."""
    if r["sinal_para_esta_semana"]:
        return ("Ficar comprado", "manter") if r["comprado"] else ("Comprar", "compra")
    return ("Vender", "venda") if r["comprado"] else ("Ficar no CDI", "fora")


# Recalcula os sinais no navegador com a semana em curso (mesma regra de scripts/bitcoin/backtest.py).
SINAIS_JS = r"""
(function(){
var box=document.getElementById('gs-box');if(!box)return;
var G=JSON.parse(document.getElementById('gs-dados').textContent);
var svg=box.querySelector('svg'),NS='http://www.w3.org/2000/svg';
var lo=+svg.dataset.lo,hi=+svg.dataset.hi,py0=+svg.dataset.py0,py1=+svg.dataset.py1,xv=+svg.dataset.xv,lv=+svg.dataset.lv;
function yp(v){v=Math.max(lo,Math.min(hi,v));return py1-(v-lo)/(hi-lo)*(py1-py0)}
function sma(c,n,i){if(i<n-1)return null;var s=0;for(var k=i-n+1;k<=i;k++)s+=c[k];return s/n}
function ema(c,n){var k=2/(n+1),o=[],e=null;c.forEach(function(x){e=e===null?x:x*k+e*(1-k);o.push(e)});return o}
function rsi(c,n){n=n||14;var o=c.map(function(){return null}),g=0,p=0;for(var i=1;i<c.length;i++){var d=c[i]-c[i-1],a=Math.max(d,0),b=Math.max(-d,0);
 if(i<=n){g+=a/n;p+=b/n;if(i==n)o[i]=p?100-100/(1+g/p):100}else{g=(g*(n-1)+a)/n;p=(p*(n-1)+b)/n;o[i]=p?100-100/(1+g/p):100}}return o}
function sinais(c){var n=c.length,s={},i,est,out,r,m,sig;
 s['Média de 40 semanas']=c.map(function(x,i){var m=sma(c,40,i);return m!==null&&x>m});
 s['Cruzamento 10 x 40 semanas']=c.map(function(x,i){var m=sma(c,40,i);return m!==null&&sma(c,10,i)>m});
 r=rsi(c);est=false;out=[];for(i=0;i<n;i++){if(r[i]!==null&&i>0&&r[i-1]!==null){if(!est&&r[i-1]<30&&30<=r[i])est=true;else if(est&&r[i-1]>70&&70>=r[i])est=false}out.push(est)}s['IFR semanal (30/70)']=out;
 est=false;out=[];for(i=0;i<n;i++){if(i>=20){if(!est&&c[i]>Math.max.apply(null,c.slice(i-20,i)))est=true;else if(est&&c[i]<Math.min.apply(null,c.slice(i-10,i)))est=false}out.push(est)}s['Rompimento 20 semanas']=out;
 var e12=ema(c,12),e26=ema(c,26);m=e12.map(function(x,i){return x-e26[i]});sig=ema(m,9);s['MACD semanal']=m.map(function(x,i){return i>=35&&x>sig[i]});
 est=false;out=[];var topo=null,fundo=null;for(i=0;i<n;i++){var j=i-2;if(j>=2){var w=c.slice(j-2,j+3);if(c[j]==Math.max.apply(null,w))topo=c[j];if(c[j]==Math.min.apply(null,w))fundo=c[j]}
  if(topo!==null&&!est&&c[i]>topo)est=true;else if(fundo!==null&&est&&c[i]<fundo)est=false;out.push(est)}s['Topos e fundos (Dow)']=out;
 est=false;out=[];var pa=null;for(i=0;i<n;i++){var pc=null;if(i>=52){var q=0;for(var k=i-52;k<i;k++)if(c[k]<c[i])q++;pc=100*q/52;if(pa!==null){if(!est&&pa<20&&20<=pc)est=true;else if(est&&pa>80&&80>=pc)est=false}}pa=pc;out.push(est)}s['Faixas de percentis 52 semanas']=out;
 var V=G.votantes;G.limites.forEach(function(K){est=true;out=[];for(i=0;i<n;i++){var v=0;V.forEach(function(x){if(s[x][i])v++});if(v>=K)est=true;else if(V.length-v>=K)est=false;out.push(est)}s['Consenso '+K+' x '+(V.length-K)]=out});
 return s}
function el(t,a){var e=document.createElementNS(NS,t);for(var k in a)e.setAttribute(k,a[k]);return e}
function br(v,d){return v.toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d})}
function desenha(sem,preco){
 // sem: velas diárias depois do último domingo fechado, agrupadas em semanas; a última é a semana em curso
 var c=G.fech.slice(),ab=G.ultimo;
 sem.forEach(function(w,ix){if(ix<sem.length-1)c.push(w.fech)});
 var at=sem[sem.length-1];at.fech=preco;at.alta=Math.max(at.alta,preco);at.baixa=Math.min(at.baixa,preco);
 if(sem.length>1)ab=sem[sem.length-2].fech;
 c.push(preco);
 var s=sinais(c),g=document.getElementById('gs-vela-viva');g.innerHTML='';
 var cls=preco>=ab?'gs-alta':'gs-baixa',y1=Math.min(yp(ab),yp(preco)),y2=Math.max(yp(ab),yp(preco));
 g.appendChild(el('line',{x1:xv,x2:xv,y1:yp(at.alta),y2:yp(at.baixa),'class':cls+' gs-viva'}));
 g.appendChild(el('rect',{x:xv-lv/2,y:y1,width:lv,height:Math.max(1,y2-y1),'class':cls+' gs-viva'}));
 document.getElementById('gs-preco').textContent='US$ '+br(preco,0)+' agora';
 document.getElementById('gs-preco').setAttribute('y',yp(preco)+4);
 var votos=0;
 G.estrategias.forEach(function(E){
  var agora=s[E.nome][c.length-1],antes=s[E.nome][c.length-2],m=document.getElementById('gs-m-'+E.i);m.innerHTML='';
  if(G.votantes.indexOf(E.nome)>=0&&agora)votos++;
  var ym=E.y+15;
  if(agora)m.appendChild(el('rect',{x:xv-lv,y:E.y+4,width:lv*2,height:22,fill:E.cor,opacity:'.22'}));
  if(agora&&!antes)m.appendChild(el('path',{d:'M'+(xv-5)+' '+(ym+5)+'L'+(xv+5)+' '+(ym+5)+'L'+xv+' '+(ym-6)+'Z','class':'gs-compra gs-pisca'}));
  if(!agora&&antes)m.appendChild(el('path',{d:'M'+(xv-5)+' '+(ym-5)+'L'+(xv+5)+' '+(ym-5)+'L'+xv+' '+(ym+6)+'Z','class':'gs-venda gs-pisca'}));
  var rot,tipo;if(agora){rot=E.comprado?'Ficar comprado':'Comprar';tipo=E.comprado?'manter':'compra'}else{rot=E.comprado?'Vender':'Ficar no CDI';tipo=E.comprado?'venda':'fora'}
  var d=document.getElementById('gs-d-'+E.i);d.textContent=rot;d.setAttribute('class','gs-dec gs-'+tipo+'-t');
  var k=document.getElementById('gs-k-'+E.i),xm=+k.dataset.x,yc=E.y+15;k.innerHTML='';
  k.appendChild(tipo=='compra'?el('path',{d:'M'+(xm-6)+' '+(yc+6)+'L'+(xm+6)+' '+(yc+6)+'L'+xm+' '+(yc-7)+'Z','class':'gs-compra'}):
   tipo=='venda'?el('path',{d:'M'+(xm-6)+' '+(yc-6)+'L'+(xm+6)+' '+(yc-6)+'L'+xm+' '+(yc+7)+'Z','class':'gs-venda'}):
   tipo=='manter'?el('circle',{cx:xm,cy:yc,r:6,fill:E.cor}):el('circle',{cx:xm,cy:yc,r:5.5,'class':'gs-fora'}));
 });
 var h=new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'});
 document.getElementById('gs-hora').textContent='Ao vivo, '+h+': '+votos+' de 7 sinais comprados se a semana fechasse agora.';
}
function semanas(velas){
 // velas da Coinbase: [t, baixa, alta, abre, fecha, vol]; semana fecha no domingo (UTC)
 var ult=new Date(G.ultima_data+'T00:00:00Z').getTime(),D=86400000,ws=[];
 velas.sort(function(a,b){return a[0]-b[0]}).forEach(function(v){var t=v[0]*1000;if(t<=ult)return;var k=Math.floor((t-ult-1)/(7*D));
  var w=ws[k]||(ws[k]={alta:v[2],baixa:v[1],fech:v[4]});w.alta=Math.max(w.alta,v[2]);w.baixa=Math.min(w.baixa,v[1]);w.fech=v[4]});
 return ws.filter(function(w){return w})}
function busca(){
 var ini=new Date(new Date(G.ultima_data+'T00:00:00Z').getTime()+86400000).toISOString().slice(0,10);
 fetch('https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start='+ini+'T00:00:00Z').then(function(r){return r.json()}).catch(function(){return[]})
 .then(function(v){var ws=semanas(Array.isArray(v)?v:[]);
  fetch('https://api.coinbase.com/v2/prices/BTC-USD/spot').then(function(r){return r.json()}).then(function(j){var p=+j.data.amount;
   if(!ws.length)ws=[{alta:p,baixa:p,fech:p}];desenha(ws,p)}).catch(function(){if(ws.length)desenha(ws,ws[ws.length-1].fech)})})}
window.gsSinais=sinais;busca();setInterval(busca,60000);
})();
"""


def grafico_semana_btc_svg(D):
    G = D.get("grafico")
    if not G:
        return ""
    est = {r["nome"]: r for r in D["estrategias"]}
    nomes = [n for n in G["sinais"] if n in est]
    nomes = [n for n in nomes if not n.startswith("Consenso")] + [n for n in nomes if n.startswith("Consenso")]
    n = len(G["fech"])
    X0, X1 = 8, 790                   # área do gráfico; à direita ficam as duas colunas de decisão
    C1, C2 = X1 + 82, X1 + 236        # "Decisão de domingo" e "Se fechasse agora"
    W = C2 + 150
    PY0, PY1 = 34, 306                # painel de preço
    L0, LH = 362, 30                  # faixas das estratégias
    H = L0 + LH * len(nomes) + 34
    passo = (X1 - X0) / (n + 1)       # uma vaga a mais: a vela da semana em curso, desenhada ao vivo
    xc = lambda i: X0 + passo * (i + .5)
    lo, hi = min(G["baixa"]), max(G["alta"])
    folga = (hi - lo) * .12
    lo, hi = lo - folga, hi + folga
    yp = lambda v: PY1 - (v - lo) / (hi - lo) * (PY1 - PY0)
    lv = max(2.0, passo * .62)
    xv = xc(n)
    out = [f'<svg class="graf-semana" viewBox="0 0 {W} {H}" data-lo="{lo:.2f}" data-hi="{hi:.2f}" data-py0="{PY0}" data-py1="{PY1}" data-xv="{xv:.1f}" data-lv="{lv:.1f}" role="img" aria-label="Velas semanais do bitcoin em dólares, com a semana em curso ao vivo, e a decisão de cada estratégia">']
    deg = 10 ** math.floor(math.log10((hi - lo) / 4))
    deg = next(d * deg for d in (1, 2, 2.5, 5, 10) if (hi - lo) / (d * deg) <= 6)
    v = math.ceil(lo / deg) * deg
    while v < hi:
        y = yp(v)
        out.append(f'<line x1="{X0}" x2="{X1}" y1="{y:.1f}" y2="{y:.1f}" class="gs-grade"/><text x="{X1 + 6}" y="{y + 4:.1f}" class="gs-eixo">US$ {v / 1000:,.0f} mil</text>'.replace(",", "."))
        v += deg
    ult_mes = None
    for i, d in enumerate(G["datas"]):
        a, m_, _ = d.split("-")
        if m_ != ult_mes and i > 0 and int(m_) % 3 == 1:
            x = xc(i)
            out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{PY0}" y2="{L0 + LH * len(nomes)}" class="gs-mes"/><text x="{x + 3:.1f}" y="{PY1 + 16}" class="gs-eixo">{MESES_ABR[int(m_) - 1]}/{a[2:]}</text>')
        ult_mes = m_
    for i in range(n):
        o, c, h, l_ = G["abre"][i], G["fech"][i], G["alta"][i], G["baixa"][i]
        cls = "gs-alta" if c >= o else "gs-baixa"
        x = xc(i)
        y1, y2 = sorted((yp(o), yp(c)))
        out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{yp(h):.1f}" y2="{yp(l_):.1f}" class="{cls}"/><rect x="{x - lv / 2:.1f}" y="{y1:.1f}" width="{lv:.1f}" height="{max(1, y2 - y1):.1f}" class="{cls}"/>')
    # semana em curso: faixa destacada, vela e preço preenchidos pelo script
    out.append(f'<rect x="{xv - passo / 2:.1f}" y="{PY0 - 8}" width="{passo:.1f}" height="{L0 + LH * len(nomes) - PY0 + 8}" class="gs-agora"/>')
    out.append(f'<text x="{xv:.1f}" y="{PY0 - 12}" text-anchor="end" class="gs-eixo">semana em curso &#9656;</text>')
    out.append(f'<g id="gs-vela-viva"></g><text id="gs-preco" x="{X1 + 6}" y="{PY0}" class="gs-eixo gs-viva-t"></text>')
    out.append(f'<text x="{X0}" y="{L0 - 12}" class="gs-tit">Sinal de cada estratégia</text>'
               f'<text x="{C1 - 8}" y="{L0 - 12}" class="gs-tit">Domingo, {data_br(G["datas"][-1])[:5]}</text>'
               f'<text x="{C2 - 8}" y="{L0 - 12}" class="gs-tit gs-viva-t">Se fechasse agora</text>')
    lista_js = []
    for j, nome in enumerate(nomes):
        y = L0 + LH * j
        cor = cor_btc(nome)
        s = G["sinais"][nome]
        out.append(f'<line x1="{X0}" x2="{X1}" y1="{y + LH - 4}" y2="{y + LH - 4}" class="gs-base"/>')
        i = 0
        while i < n:
            if s[i]:
                k = i
                while k < n and s[k]:
                    k += 1
                out.append(f'<rect x="{X0 + passo * i:.1f}" y="{y + 4}" width="{passo * (k - i):.1f}" height="{LH - 8}" fill="{cor}" opacity=".22"/>')
                i = k
            else:
                i += 1
        ant = G["sinal_anterior"].get(nome, s[0])
        for i in range(n):
            if s[i] != ant:
                x, ym = xc(i), y + LH / 2
                if s[i]:
                    out.append(f'<path d="M{x - 5:.1f} {ym + 5:.1f}L{x + 5:.1f} {ym + 5:.1f}L{x:.1f} {ym - 6:.1f}Z" class="gs-compra"><title>{e(nome)}: compra em {e(data_br(G["datas"][i]))}</title></path>')
                else:
                    out.append(f'<path d="M{x - 5:.1f} {ym - 5:.1f}L{x + 5:.1f} {ym - 5:.1f}L{x:.1f} {ym + 6:.1f}Z" class="gs-venda"><title>{e(nome)}: venda em {e(data_br(G["datas"][i]))}</title></path>')
            ant = s[i]
        out.append(f'<g id="gs-m-{j}"></g>')
        out.append(f'<text x="{X0 + 4}" y="{y + 15}" class="gs-nome{" gs-forte" if nome.startswith("Consenso") else ""}" fill="{cor}">{e(nome)}</text>')
        rot, tipo = decisao_btc(est[nome])
        ym = y + LH / 2
        xm = C1
        marca = {"compra": f'<path d="M{xm - 6} {ym + 6}L{xm + 6} {ym + 6}L{xm} {ym - 7}Z" class="gs-compra"/>',
                 "venda": f'<path d="M{xm - 6} {ym - 6}L{xm + 6} {ym - 6}L{xm} {ym + 7}Z" class="gs-venda"/>',
                 "manter": f'<circle cx="{xm}" cy="{ym}" r="6" fill="{cor}"/>',
                 "fora": f'<circle cx="{xm}" cy="{ym}" r="5.5" class="gs-fora"/>'}[tipo]
        out.append(f'{marca}<text x="{xm + 14}" y="{ym + 4.5}" class="gs-dec gs-{tipo}-t">{rot}</text>')
        out.append(f'<g id="gs-k-{j}" data-x="{C2}"><circle cx="{C2}" cy="{ym}" r="5.5" class="gs-fora"/></g><text id="gs-d-{j}" x="{C2 + 14}" y="{ym + 4.5}" class="gs-dec gs-fora-t">carregando…</text>')
        lista_js.append({"i": j, "nome": nome, "cor": cor, "y": y, "comprado": bool(est[nome]["comprado"])})
    out.append(f'<text x="{X0}" y="{H - 8}" class="gs-eixo">▲ compra  ▼ venda  · faixa colorida: comprado  · ● ficar comprado  ○ ficar no CDI. Fonte: Coinbase (BTC-USD; semana fecha no domingo, UTC).</text>')
    out.append("</svg>")
    dados = {"fech": G["hist_fech"], "ultimo": G["fech"][-1], "ultima_data": G["datas"][-1],
             "limites": G["consenso_limites"], "votantes": G["votantes"], "estrategias": lista_js}
    return f'''    <h3 class="conceito-tit" id="grafico-semana">O gráfico da semana: a decisão de cada estratégia</h3>
    <p>Velas semanais do último ano e meio, em dólares, com a semana em curso desenhada ao vivo. Embaixo, uma faixa por estratégia: o trecho colorido é quando ela esteve comprada, ▲ marca a semana em que mandou comprar e ▼ a semana em que mandou vender. À direita, a decisão tomada no último domingo e a que sairia se a semana fechasse agora, recalculada a cada minuto com o preço da Coinbase. Só a decisão de domingo vale: a prévia muda até o fechamento.</p>
    <p class="nota-min gs-viva-t" id="gs-hora">Carregando o preço ao vivo…</p>
    <div class="tab-rolagem graf-semana-box" id="gs-box">
{"".join(out)}
    </div>
    <script type="application/json" id="gs-dados">{json.dumps(dados, ensure_ascii=False, separators=(",", ":"))}</script>
    <script>{SINAIS_JS}</script>
'''



def consenso_btc_html(D):
    C = D.get("consenso")
    if not C:
        return ""
    votos = "".join(f'<li class="{"sim" if v else "nao"}"><i class="cor" style="background:{cor_btc(n)}"></i>{e(n)}: <b>{"comprado" if v else "fora"}</b></li>' for n, v in C["votos_por_sinal"].items())
    return f"""    <h3 class="conceito-tit">O placar dos sete sinais: {C['votos_agora']} de 7 comprados no domingo</h3>
    <p>As quatro estratégias de consenso não inventam nada: só ouvem os sete sinais dos autores e mudam de posição quando o placar chega ao mínimo de cada uma. <b>7 x 0</b> exige unanimidade; <b>6 x 1</b> aceita um voto contra; <b>5 x 2</b>, dois; <b>4 x 3</b> segue a maioria simples. Enquanto o placar não chega lá, a estratégia espera na posição em que está.</p>
    <ul class="placar">{votos}</ul>
"""


def curvas_btc_svg(D):
    datas = D["curvas"]["datas"]
    nomes = [x["nome"] for x in D["estrategias"]]
    w, h, pl, pr, pt, pb = 760, 340, 64, 12, 10, 26
    vals = [v for n in nomes for v in D["curvas"][n] if v > 0]
    lo = math.floor(math.log10(max(min(vals), 1e-3)) * 2) / 2
    hi = max(math.ceil(math.log10(max(vals)) * 2) / 2, 0.5)
    n = len(datas) - 1
    X = lambda i: pl + i * (w - pl - pr) / n
    Y = lambda v: pt + (hi - math.log10(max(v, 1e-3))) * (h - pt - pb) / (hi - lo)
    grade = []
    for k in range(int(math.ceil(lo)), int(math.floor(hi)) + 1):
        v = 10 ** k
        grade.append(f'<line x1="{pl}" x2="{w - pr}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="{"g1" if k == 0 else "g"}"/>'
                     f'<text x="{pl - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{str(v).replace(".", ",")} BTC</text>')
    anos = []
    for i, d in enumerate(datas):
        if i and d[:4] != datas[i - 1][:4] and int(d[:4]) % 2 == 0:
            anos.append(f'<text x="{X(i):.1f}" y="{h - 6}" text-anchor="middle">{d[:4]}</text>')
    linhas = []
    for nome in sorted(nomes, key=lambda x: x == "Comprar e segurar"):
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(D["curvas"][nome]))
        largura = 2.4 if nome == "Comprar e segurar" or nome.startswith("Consenso") else 1.5
        linhas.append(f'<polyline points="{pts}" fill="none" stroke="{cor_btc(nome)}" stroke-width="{largura}"><title>{e(nome)}</title></polyline>')
    leg = "".join(f'<span><i style="background:{cor_btc(x)}"></i>{e(x)}</span>' for x in nomes)
    return (f'<svg class="curvas-btc" viewBox="0 0 {w} {h}" role="img" aria-label="Quanto bitcoin cada estratégia teria, semana a semana, em escala logarítmica">'
            + "".join(grade) + "".join(anos) + "".join(linhas) + f'</svg>\n    <div class="legenda-btc">{leg}</div>')


def acompanhamento_btc_html():
    arq = os.path.join(SITE, "bitcoin", "dados.json")
    if not os.path.exists(arq):
        return ""
    D = json.load(open(arq, encoding="utf-8"))

    def pct(x):
        return f"{x * 100:+.1f}%".replace(".", ",")

    def br(d):
        return f"{d[8:10]}/{d[5:7]}/{d[:4]}"

    def num(x, k):
        return f"{x:,.{k}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    p0 = D["ultimo_fech_brl"]
    linhas = []
    for r in sorted(D["estrategias"], key=lambda x: -x["btc_final"]):
        cls = ' class="regua"' if r["nome"] == "Comprar e segurar" else ' class="consenso"' if r["nome"].startswith("Consenso") else ""
        pos = "Comprado" if r["comprado"] else "No CDI"
        if r["nome"] == "Só CDI":
            prox = "Ficar no CDI"
        elif r["sinal_para_esta_semana"]:
            prox = "Ficar comprado" if r["comprado"] else "Comprar"
        else:
            prox = "Vender" if r["comprado"] else "Ficar no CDI"
        v0 = r["valor_inicio_acomp_brl"] or 0
        v = r["btc"] * p0 + r["caixa_brl"]
        ret = pct(v / v0 - 1) if v0 else "–"
        linhas.append(
            f'        <tr{cls} data-btc="{r["btc"]:.8f}" data-caixa="{r["caixa_brl"]:.2f}" data-v0="{v0:.2f}">\n'
            f'          <td><i class="cor" style="background:{cor_btc(r["nome"])}"></i>{e(r["nome"])}</td>\n'
            f'          <td>{pos}<small>desde {br(r["desde"])}</small></td>\n'
            f'          <td class="num vivo-btc">{num(v / p0, 3)}</td>\n'
            f'          <td class="num vivo-ret">{ret}</td>\n'
            f'          <td>{prox}</td>\n'
            f'          <td class="num">{num(r["btc_final"], 2)}</td>\n'
            f'          <td class="num">{pct(r["pior_queda"])}</td>\n'
            f'        </tr>')
    ini, fim, ia = br(D["inicio"]), br(D["fim"]), br(D["inicio_acompanhamento"])
    tv = ('{"container_id":"tv-btc","symbol":"COINBASE:BTCUSD","interval":"W","timezone":"America/Sao_Paulo","theme":"light",'
          '"style":"1","locale":"br","autosize":true,"hide_side_toolbar":true,"allow_symbol_change":false,'
          '"studies":["MASimple@tv-basicstudies","MACD@tv-basicstudies"]}')
    js = ("(function(){var ptax=" + f"{D['ptax']:.4f}" + ";"
          "function f(p){document.getElementById('btc-agora').textContent='R$ '+Math.round(p).toLocaleString('pt-BR');"
          "document.getElementById('btc-hora').textContent='(agora, '+new Date().toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'})+')';"
          "document.querySelectorAll('.tab-btc tbody tr').forEach(function(tr){var b=+tr.dataset.btc,c=+tr.dataset.caixa,v0=+tr.dataset.v0,v=b*p+c;"
          "tr.querySelector('.vivo-btc').textContent=(v/p).toFixed(3).replace('.',',');"
          "if(v0){var r=(v/v0-1)*100,td=tr.querySelector('.vivo-ret');td.textContent=(r>=0?'+':'')+r.toFixed(1).replace('.',',')+'%';td.className='num vivo-ret '+(r>=0?'sobe':'desce')}})}"
          "function busca(){fetch('https://api.coinbase.com/v2/prices/BTC-BRL/spot').then(function(r){return r.json()}).then(function(j){f(+j.data.amount)})"
          ".catch(function(){fetch('https://api.coinbase.com/v2/prices/BTC-USD/spot').then(function(r){return r.json()}).then(function(j){f(+j.data.amount*ptax)}).catch(function(){})})}"
          "busca();setInterval(busca,60000)})();")
    return f"""  <section class="para-quem" id="ao-vivo">
    <h2>Acompanhamento ao vivo</h2>
    <p>Bitcoin agora: <b id="btc-agora">R$ {num(p0, 0)}</b> <small class="nota-min" id="btc-hora">(fechamento de {fim})</small></p>
    <div class="tv-box">
      <div class="tradingview-widget-container"><div id="tv-btc"></div></div>
      <script src="https://s3.tradingview.com/tv.js"></script>
      <script>if(window.TradingView)new TradingView.widget({tv});</script>
    </div>
{grafico_semana_btc_svg(D)}
{consenso_btc_html(D)}
    <div class="tab-rolagem">
    <table class="tab-btc">
      <thead><tr><th>Estratégia</th><th>Posição</th><th class="num">BTC agora</th><th class="num">Desde {ia}</th><th>Decisão de domingo</th><th class="num">BTC no fim do teste</th><th class="num">Pior queda</th></tr></thead>
      <tbody>
{chr(10).join(linhas)}
      </tbody>
    </table>
    </div>
    <p class="nota-min">“BTC agora” e “Desde {ia}” mudam com o preço ao vivo, atualizado a cada minuto. As duas últimas colunas vêm do teste no histórico, de {ini} a {fim}: cada estratégia começa com 1 BTC, paga {num(D['taxa_por_operacao'] * 100, 2)}% por operação e rende CDI quando está fora. A decisão de domingo é o que cada sinal manda fazer no próximo fechamento semanal. Fontes: {e(D['fontes']['btc'])}; dólar e CDI do Banco Central. Atualizado em {e(D['gerado_em'])}.</p>
    <h3 class="conceito-tit">Quanto bitcoin cada estratégia teria, semana a semana</h3>
    {curvas_btc_svg(D)}
    <p class="nota-min">Escala logarítmica. Acima da linha de 1 BTC, a estratégia ganhou de quem só comprou e segurou.</p>
    <script>{js}</script>
  </section>
"""


def pagina_bitcoin():
    rel = "../"
    arq = [("1889-um-dolar-honesto", "1889", "Um dólar honesto: a moeda que compra sempre o mesmo"),
           ("1892-a-questao-da-prata", "1892", "Taussig e a prata que voltava ao Tesouro"),
           ("1896-lexis-situacao-monetaria", "1895", "Lexis: por que o bimetalismo seria um salto no escuro"),
           ("1896-valorizacao-e-juros", "1896", "Fisher: o juro que antecipa o valor da moeda"),
           ("1899-kinder-padrao-monetario-e-distribuicao", "1899", "Kinder: quem ganhou e quem perdeu com a queda dos preços")]
    lis = "\n".join(f'      <li><a href="{rel}arquivo/{sl}/"><b>{a}</b> · {e(t)}</a></li>' for sl, a, t in arq)
    estrategias = [
        ("Comprar e segurar (a régua)", "Compra no início e nenhuma venda. Todo sinal técnico precisa bater esta régua para valer o trabalho."),
        ("Média móvel de 40 semanas", "Comprado com o fechamento semanal acima da média, fora abaixo dela. É a versão semanal da famosa média de 200 dias."),
        ("Cruzamento das médias de 10 e 40 semanas", "Entra quando a média curta cruza a longa para cima e sai no cruzamento para baixo. O equivalente semanal do cruzamento de 50 e 200 dias."),
        ("IFR semanal", "Compra quando o índice de força relativa do gráfico semanal indica sobrevenda e vende na sobrecompra. Testa se o exagero do mercado se corrige."),
        ("Rompimento de 20 semanas", "Entra quando o fechamento semanal rompe a máxima das últimas 20 semanas e sai quando perde a mínima de 10. Testa se tendência forte continua forte."),
        ("Topos e fundos ascendentes (Dow)", "Comprado enquanto cada topo semanal supera o anterior; sai quando um fundo fica abaixo do fundo anterior. É a regra de Dow para a tendência primária, aplicada ao gráfico semanal."),
        ("Faixas de percentis de 52 semanas", "Compra quando o fechamento semanal volta para cima do percentil 20 do último ano e reduz quando perde força acima do percentil 80. Testa os limites de força compradora e vendedora."),
        ("MACD semanal", "Segue o cruzamento do MACD semanal com a sua linha de sinal. Testa o indicador de momento mais popular dos gráficos."),
    ]
    est = "\n".join(f"""    <li>
      <span class="passo-num">{k}</span>
      <h2>{e(n)}</h2>
      <p>{e(t)}</p>
    </li>""" for k, (n, t) in enumerate(estrategias, 1))
    corpo = f"""
<main class="env pagina-min">
  <section class="heroi heroi-interno">
    <p class="heroi-quem">Bitcoin · piloto · Renato W. Gomes, economista</p>
    <h1>Análise técnica no bitcoin, uma vez por semana: o que funciona quando a gente testa?</h1>
    <p class="heroi-olho">Uma plataforma aberta: médias móveis, IFR, rompimentos e MACD, no gráfico semanal. Cada sinal é testado no histórico de preços do bitcoin, comparado com simplesmente comprar e segurar e com o CDI, e depois acompanhado ao vivo, semana a semana, com o retorno, o risco e a pior queda à vista.</p>
    <p class="heroi-acoes"><a class="botao botao-cheio" href="#contato">Receber os resultados</a> <a class="botao" href="#estrategias">Ver as estratégias</a></p>
  </section>

  <section class="para-quem" id="estrategias">
    <h2>Os sinais em teste</h2>
    <p>Todos partem da mesma posição de referência: <b>1 bitcoin</b>. Quando o sinal manda sair, o valor vai para o CDI; quando manda voltar, recompra o que der. No fim, a pergunta é simples: o sinal terminou com mais ou menos de 1 bitcoin?</p>
    <p><b>Acompanhamento semanal.</b> Os sinais olham só o gráfico semanal e são conferidos uma vez por semana, no fechamento de domingo para segunda. Nada de operar no meio da semana: menos ruído, menos taxa e uma rotina que qualquer pessoa consegue seguir.</p>
  </section>
  <ol class="passos">
{est}
  </ol>

{acompanhamento_btc_html()}
{diario_btc_html()}
  <section class="para-quem">
    <h2>Como eu meço</h2>
    <ul class="lista-min">
      <li><b>Em bitcoin, em reais e em dólares.</b> Em bitcoin, a régua é a posição inicial de 1 BTC: quem termina com menos perdeu para quem só segurou. Em reais, o câmbio muda o resultado para quem mora no Brasil.</li>
      <li><b>Retorno, volatilidade e pior queda.</b> Ganhar muito não basta se a queda no caminho faz o investidor desistir.</li>
      <li><b>Contra o CDI.</b> Toda estratégia precisa bater a renda fixa para se justificar.</li>
      <li><b>Custos incluídos.</b> Cada compra e venda paga taxa de corretora; sinal que opera demais pode perder para quem não faz nada.</li>
      <li><b>Teste no passado, acompanhamento no presente.</b> O histórico mostra o que teria acontecido; o acompanhamento mostra o que está acontecendo, sem ajustar a regra depois do fato.</li>
      <li><b>Fonte dos preços sempre indicada</b>, e os números de cada teste disponíveis para quem quiser conferir.</li>
    </ul>
    <p class="nota-min">Piloto: primeiros resultados em preparação. Regras e parâmetros podem mudar até o fim do piloto, e cada mudança fica registrada.</p>
  </section>

{conceitos_btc_html()}
{autores_btc_html(rel)}
  <section class="para-quem" id="fontes">
    <h2>As fontes</h2>
    <p>Em 31 de outubro de 2008, Satoshi Nakamoto publicou <a href="https://bitcoin.org/bitcoin.pdf" target="_blank" rel="noopener"><i>Bitcoin: A Peer-to-Peer Electronic Cash System</i></a> (“Bitcoin: um sistema de dinheiro eletrônico ponto a ponto”). E a pergunta de fundo, o que acontece quando a quantidade de moeda não pode crescer à vontade, foi debatida com dados no fim do século XIX. No Arquivo:</p>
    <ul class="lista-min">
{lis}
    </ul>
  </section>

  <p class="nota-min">Conteúdo de estudo. Resultado passado não garante resultado futuro, e nada aqui é recomendação de investimento.</p>

  {bloco_contato("Resultados de bitcoin (/bitcoin)", "Quer receber os resultados quando saírem, ou sugerir uma estratégia para testar? Deixe seu contato.", "Qual sinal ou indicador você gostaria de ver testado?", "bitcoin/", "Receba os resultados")}
</main>
"""
    escreve("bitcoin", cabeca("Bitcoin: análise técnica testada — Renato W. Gomes, economista", "Piloto: sinais de análise técnica no bitcoin (médias móveis, IFR, rompimentos, MACD) testados no histórico e acompanhados ao vivo, contra comprar e segurar e contra o CDI.", "bitcoin/", rel)
            + topo("bitcoin/", rel) + corpo + rodape(rel))


def pagina_historia():
    rel = "../"
    livros = "\n".join(f"""    <article class="cartao colecao">
      <a href="{rel}leituras/{L['slug']}/">
        <span class="chapeu">{e(L['autor'])} · {L['ano']}</span>
        <h3 class="tit tit-g">{e(L['titulo'])}</h3>
        <p class="olho">{e(L['chamada'])}</p>
        <span class="selo">{len(L.get('resenhas', []))} de {len(L['capitulos'])} capítulos resenhados</span>
      </a>
    </article>""" for L in LIVROS)
    docs = ""
    if DOCS_PUB:
        docs = ('  <div class="faixa">\n    <h2>Documentos de época</h2>\n    <span class="sub">Obras antigas resenhadas como documento histórico</span>\n  </div>\n'
                '  <section class="grade-3">\n' + "\n".join(cartao_documento(d, rel) for d in DOCS_PUB) + '\n  </section>\n')
    corpo = f"""
<main class="env">
  <section class="heroi heroi-interno">
    <p class="heroi-quem">História · Renato W. Gomes, economista</p>
    <h1>A história econômica, lida livro a livro.</h1>
    <p class="heroi-olho">Obras longas de história e de pensamento econômico, resenhadas na ordem, um capítulo por página: o argumento do autor em português, os fatos citados e a pergunta de hoje.</p>
  </section>
  <section class="grade-3">
{livros}
  </section>
{docs}
  <div style="height:64px"></div>
</main>
"""
    escreve("historia", cabeca("História — livros de história econômica comentados · Renato W. Gomes", "Obras de história e pensamento econômico resenhadas capítulo a capítulo, em português, com a página citada.", "historia/", rel)
            + topo("historia/", rel) + corpo + rodape(rel))


def pagina_economia():
    rel = "../"
    cards = "\n".join(cartao_colecao(c, "../arquivo/") for c in COLECOES)
    recentes = "\n".join(cartao_edicao(ed, rel) for ed in edicoes_de("eua")[-3:][::-1])
    corpo = f"""
<main class="env">
  <section class="heroi heroi-interno">
    <p class="heroi-quem">Economia · Renato W. Gomes, economista</p>
    <h1>Os periódicos que criaram a economia moderna, comentados em português.</h1>
    <p class="heroi-olho">Monopólios, ferrovias, moeda, impostos e o papel do Estado, discutidos por quem viveu a primeira grande era dos trustes. Edição por edição, com o documento original a um clique.</p>
    <p class="heroi-acoes"><a class="botao botao-cheio" href="../arquivo/eua/">Começar pela primeira edição</a> <a class="botao" href="../ensaios/">Ler os ensaios</a></p>
  </section>
  <div class="faixa"><h2>Mais recentes</h2><a class="mais" href="../arquivo/">Arquivo completo &rarr;</a></div>
  <section class="grade-3">
{recentes}
  </section>
  <div class="faixa"><h2>Coleções</h2><span class="sub">Estados Unidos, China e Europa</span></div>
  <section class="grade-3">
{cards}
  </section>
  <p class="olho" style="margin:8px 0 64px;font-size:15px">Também: <a href="../notas/">Notas · Então × Agora</a>, um dado histórico ao lado de um dado atual. Documentos em domínio público, via JSTOR Early Journal Content e Internet Archive; sem afiliação com as instituições que publicaram os originais.</p>
</main>
"""
    escreve("economia", cabeca("Economia — os periódicos clássicos comentados · Renato W. Gomes", "Os periódicos que criaram a economia moderna, de 1886 em diante, lidos no original e comentados em português.", "economia/", rel)
            + topo("economia/", rel) + corpo + rodape(rel))


NUMEROS_MS = ["comercio-servicos-e-industrias", "funcionalismo", "arrecadacao-tributaria", "educacao", "moradia", "mobilidade-e-transporte"]


def pagina_ms():
    """Mato Grosso do Sul: página de entrada própria. Reúne Campo Grande (livro, situação, notícias) e as contas públicas."""
    rel = "../"
    caps = {c["slug"]: c for c in CG["capitulos"]} if CG else {}
    linhas = []
    for sl in NUMEROS_MS:
        c = caps.get(sl)
        if not c or not c.get("indicador"):
            continue
        i = c["indicador"]
        linhas.append(f"""    <li>
      <p class="ms-valor">{e(i['valor'].rstrip(','))}</p>
      <p class="ms-texto">{e(i['texto'])} <a href="../campo-grande/livro/{sl}/">{e(c['titulo'])}</a></p>
      <p class="ms-fonte">Fonte: {e(i['fonte'])}</p>
    </li>""")
    numeros = "\n".join(linhas)
    corpo = f"""
<main class="env pagina-min">
  <section class="heroi heroi-interno">
    <p class="heroi-quem">Mato Grosso do Sul · Renato W. Gomes, economista</p>
    <h1>Mato Grosso do Sul, com o documento na mesa.</h1>
    <p class="heroi-olho">O estado e a capital lidos nas fontes oficiais: orçamento, folha, arrecadação, serviços e obras. Cada número vem com o documento de onde saiu, e quando o dado não existe, o texto diz que não existe.</p>
    <p class="heroi-acoes"><a class="botao botao-cheio" href="../campo-grande/situacao-atual/">Campo Grande hoje</a> <a class="botao" href="#numeros">Os números</a></p>
  </section>

  <div class="faixa" id="numeros"><h2>Campo Grande em seis números</h2><a class="mais" href="../campo-grande/situacao-atual/">Todos os temas &rarr;</a></div>
  <ul class="ms-numeros">
{numeros}
  </ul>

  <div class="faixa"><h2>Nesta seção</h2></div>
  <ol class="passos">
    <li>
      <span class="passo-num">1</span>
      <h2><a href="../campo-grande/situacao-atual/">Campo Grande, tema a tema</a></h2>
      <p>Como a capital está hoje em economia, contas da prefeitura, saúde, educação, moradia, transporte e segurança, com o número mais recente conferido e a fonte.</p>
    </li>
    <li>
      <span class="passo-num">2</span>
      <h2><a href="../campo-grande/livro/">{e(CG['titulo']) if CG else 'Campo Grande em 2036'}</a></h2>
      <p>Um livro em construção: o diagnóstico de cada tema e o que fazer até 2036, com o quadro das sete regiões urbanas.</p>
    </li>
    <li>
      <span class="passo-num">3</span>
      <h2><a href="../campo-grande/noticias/">Notícias que importam</a></h2>
      <p>Os fatos que mexem com a vida da cidade e do estado, cada um com a fonte original e um comentário curto.</p>
    </li>
    <li>
      <span class="passo-num">4</span>
      <h2>Contas do Estado</h2>
      <p>Em preparação: orçamento, arrecadação de ICMS, renúncia fiscal, dívida e investimento do governo de Mato Grosso do Sul, pela LOA, pelo SICONFI e pela SEFAZ-MS.</p>
    </li>
  </ol>

  <p class="olho" style="margin:8px 0 64px;font-size:15px">Análise trata da decisão administrativa, nunca da pessoa. Correções são publicadas no próprio texto, com data.</p>
</main>
"""
    escreve("ms", cabeca("Mato Grosso do Sul, com documento na mesa · Renato W. Gomes", "Mato Grosso do Sul e Campo Grande lidos nas fontes oficiais: orçamento, folha, arrecadação e serviços, cada número com o documento de origem.", "ms/", rel)
            + topo("ms/", rel) + corpo + rodape(rel))


def pagina_sobre():
    rel = "../"
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu">Sobre</span>
    <h1>Quem escreve, e com que método</h1>
    <p class="olho">Economista há quinze anos, consultor independente com especialização em finanças pela Fundação Getúlio Vargas.</p>
  </div>
  <figure class="artigo-figura">
    <img src="{rel}assets/entrevista-palacios.jpg" alt="Renato W. Gomes em entrevista" style="aspect-ratio:16/9;object-fit:cover">
    <figcaption><b>Renato W. Gomes</b>, economista, em entrevista. <span class="credito">Foto: Miguel Palacios</span></figcaption>
  </figure>
  <div class="corpo">
    <h2>Trajetória</h2>
    <p>Sou economista há quinze anos, consultor independente com especialização em Finanças pela Fundação Getúlio Vargas. Trabalho com planejamento contábil, tributário e financeiro de empresas e atuei no mercado financeiro no Rio de Janeiro e em Brasília.</p>
    <p>Desde 2020 publico análises econômicas no Instagram, como <a href="https://instagram.com/economistarenato" target="_blank" rel="noopener">@economistarenato</a>. Este site é a extensão desse trabalho, com espaço para o que não cabe num vídeo curto: o documento, a tabela e a fonte.</p>

    <h2>Economia pelas fontes</h2>
    <p>Muito do que se discute hoje — monopólio, concessão, tarifa, imposto, o tamanho do Estado — foi discutido com rigor há mais de um século, por economistas que tinham diante de si a primeira grande era dos trustes. Ler esses textos no original é uma forma de entender o presente sem slogans. Por isso este site combina dois trabalhos: os clássicos comentados, no <a href="../arquivo/">Arquivo</a>, e as contas públicas de hoje, nas <a href="../analises/">Análises</a>.</p>

    <h2 id="metodo">Como eu apuro os números</h2>
    <ol>
      <li><b>Fonte primária, sempre.</b> Documento histórico no original; lei orçamentária, LDO, Diário Oficial, portais de transparência, SICONFI/RREO, IBGE e órgãos de controle. Número de terceiro só entra depois de conferido no documento de origem.</li>
      <li><b>A fonte fica visível.</b> Cada texto termina com a lista de documentos usados, para que qualquer leitor refaça o caminho.</li>
      <li><b>O que não existe é dito.</b> Quando um dado não é publicado, o texto registra a ausência em vez de estimar por conta própria.</li>
      <li><b>Decisão, não pessoa.</b> A análise trata do ato e do desenho institucional, nunca da biografia de ninguém.</li>
      <li id="correcoes"><b>Erro se corrige na frente.</b> Correções entram no próprio texto, com data e nota do que mudou.</li>
    </ol>
  </div>
</article>
<div class="env">
  {assine()}
</div>
"""
    escreve("sobre", cabeca("Sobre — Economista Renato Gomes", "Renato W. Gomes, economista (CORECON-MS 1297), consultor independente com especialização em finanças pela FGV. Trajetória e método.", "sobre/", rel)
            + topo("sobre/", rel, completo=False) + corpo + rodape(rel))


def pagina_obrigado():
    rel = "../"
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:60px auto">
    <span class="chapeu">Obrigado</span>
    <h1>Recebido.</h1>
    <p class="olho">Sua mensagem chegou. Eu respondo por e-mail em até dois dias úteis.</p>
    <p><a class="botao botao-cheio" id="voltar" href="../">Voltar</a></p>
    <script>var d=new URLSearchParams(location.search).get('de');if(/^[a-z]+[/]$/.test(d||''))document.getElementById('voltar').href='../'+d;</script>
  </div>
</main>
"""
    escreve("obrigado", cabeca("Obrigado — Economista Renato Gomes", "Mensagem recebida.", "obrigado/", rel) + topo("", rel) + corpo + rodape(rel))


# ------------------------------------------------------------------ Leituras · Livros comentados
# Um JSON por livro em scripts/leituras/<slug>.json: ficha do livro, mapa das partes, lista de capítulos
# e as resenhas publicadas ("resenhas"). Página do livro em /leituras/<livro>/, uma página por capítulo
# resenhado em /leituras/<livro>/<slug-da-resenha>/.
LEIT_DIR = os.path.join(RAIZ, "scripts", "leituras")
LIVROS = [json.load(open(os.path.join(LEIT_DIR, f), encoding="utf-8"))
          for f in sorted(os.listdir(LEIT_DIR)) if f.endswith(".json") and not f.startswith("_")] if os.path.isdir(LEIT_DIR) else []


def ficha_livro(L):
    linhas = [("Autor", L["autor"]), ("Editora", f"{L['editora']}, {L['local']}, {L['ano']}"), ("Extensão", f"{L['paginas']} páginas")]
    if L.get("isbn"): linhas.append(("ISBN", L["isbn"]))
    dd = "".join(f"<dt>{e(a)}</dt><dd>{e(b)}</dd>" for a, b in linhas)
    compra = f'<dt>Onde comprar</dt><dd><a href="{L["compra_url"]}" target="_blank" rel="noopener">{e(L["compra_nome"])}</a>{" ou qualquer livraria, pelo ISBN" if L.get("isbn") else ""}</dd>'
    return f'    <div class="ficha-livro">\n      <h3>Ficha do livro</h3>\n      <dl>{dd}{compra}</dl>\n    </div>'


def nota_resenha(L):
    return (f"Resenha: resumo e comentário do autor deste site, em suas próprias palavras. As teses apresentadas são de "
            f"{L['autor']}, atribuídas a ele. As citações são curtas, traduzidas, com a página indicada; o texto integral não é reproduzido aqui. "
            f"“{L['titulo']}” © {L['ano']} {L['autor']} / {L['editora']}. Para o argumento completo, leia o livro.")


def cartao_resenha(L, r, rel):
    return f"""    <article class="cartao">
      <a href="{rel}leituras/{L['slug']}/{r['slug']}/">
        <span class="chapeu">{e(L['titulo'])} · Capítulo {r['numero']}</span>
        <h3 class="tit tit-g">{e(r['titulo'])}</h3>
        <p class="olho">{e(r['chamada'])}</p>
        <span class="selo">Leitura: {minutos(r)} min</span>
      </a>
    </article>"""


def pagina_leituras():
    rel = "../"
    cards = []
    for L in LIVROS:
        n = len(L.get("resenhas", []))
        cards.append(f"""    <article class="cartao colecao">
      <a href="{L['slug']}/">
        <span class="chapeu">{e(L['autor'])} · {L['ano']}</span>
        <h3 class="tit tit-g">{e(L['titulo'])}</h3>
        <p class="olho">{e(L['chamada'])}</p>
        <span class="selo">{n} de {len(L['capitulos'])} capítulos resenhados</span>
      </a>
    </article>""")
    docs_bloco = ""
    if DOCS_PUB:
        docs_bloco = ('  <div class="faixa">\n    <h2>Documentos de época</h2>\n    <span class="sub">Obras antigas resenhadas como documento histórico, com Nota do editor</span>\n  </div>\n'
                      '  <section class="grade-3">\n' + "\n".join(cartao_documento(d, rel) for d in DOCS_PUB) + '\n  </section>\n')
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:40px auto 10px">
    <span class="chapeu">Leituras · Livros comentados</span>
    <h1>Livros lidos capítulo a capítulo</h1>
    <p class="olho">Obras longas de história e de pensamento econômico, resenhadas na ordem, um capítulo por página: o argumento do autor em português, os fatos citados, um glossário e a pergunta de hoje.</p>
  </div>
  <section class="grade-3">
{chr(10).join(cards)}
  </section>
{docs_bloco}
  {assine("Um capítulo novo por semana, no seu e-mail.", "A resenha em português, com a página do livro e a ponte com o debate de hoje.")}
</main>
"""
    escreve("leituras", cabeca("Leituras · Livros comentados — Economista Renato Gomes",
                               "Obras de história e pensamento econômico resenhadas capítulo a capítulo, em português, com a página citada.", "leituras/", rel)
            + topo("leituras/", rel, completo=False) + corpo + rodape(rel))


def pagina_livro(L):
    rel = "../../"
    publicadas = {r["numero"]: r for r in L.get("resenhas", [])}
    partes = []
    for pt in L["partes"]:
        a, b = pt["capitulos"]
        lis = []
        for c in L["capitulos"]:
            if not (a <= c["numero"] <= b): continue
            r = publicadas.get(c["numero"])
            nome = f'{c["numero"]}. {e(c["titulo_pt"])}'
            if r:
                lis.append(f'          <li><a href="{r["slug"]}/"><b>{nome}</b></a> <span class="cap-meta">{e(c["paginas"])} · {minutos(r)} min</span></li>')
            else:
                lis.append(f'          <li class="cap-futuro">{nome} <span class="cap-meta">{e(c["paginas"])} · em breve</span></li>')
        partes.append(f"""    <section class="parte-livro">
      <h3>Parte {pt['numero']} · {e(pt['titulo'])} <span class="cap-meta">caps. {a}–{b}</span></h3>
      <p>{e(pt['descricao'])}</p>
      <ol class="lista-caps" start="{a}">
{chr(10).join(lis)}
      </ol>
    </section>""")
    ult = L.get("resenhas", [])[-3:][::-1]
    recentes = "\n".join(cartao_resenha(L, r, rel) for r in ult)
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu">Leituras · Livros comentados</span>
    <h1>{e(L['titulo'])}</h1>
    <p class="subtitulo-livro">{e(L['subtitulo'])}</p>
    <p class="olho">{e(L['chamada'])}</p>
  </div>
  <div class="corpo">
{ficha_livro(L)}
{render_blocos(L['blocos'])}
  </div>
</article>
<main class="env">
  <div class="faixa">
    <h2>Resenhas mais recentes</h2>
    <span class="sub">Na ordem do livro</span>
  </div>
  <section class="grade-3">
{recentes}
  </section>
  <div class="faixa">
    <h2>O livro, capítulo a capítulo</h2>
    <span class="sub">{len(publicadas)} de {len(L['capitulos'])} resenhados</span>
  </div>
  <div class="mapa-livro">
{chr(10).join(partes)}
  </div>
  <div class="corpo" style="max-width:820px;margin:0">
    <p class="nota-legal">{e(nota_resenha(L))}</p>
  </div>
  {assine("Um capítulo novo por semana, no seu e-mail.", "A resenha em português, com a página do livro e a ponte com o debate de hoje.")}
</main>
"""
    escreve(f"leituras/{L['slug']}", cabeca(f"{L['titulo']}, de {L['autor']} — Leituras · Economista Renato Gomes", L["chamada"], f"leituras/{L['slug']}/", rel)
            + topo("leituras/", rel, completo=False) + corpo + rodape(rel))


def pagina_resenha(L, r, anterior, proxima):
    rel = "../../../"
    nav = []
    if anterior: nav.append(f'<a href="../{anterior["slug"]}/">&larr; Cap. {anterior["numero"]} · {e(anterior["titulo"])}</a>')
    if proxima: nav.append(f'<a href="../{proxima["slug"]}/">Cap. {proxima["numero"]} · {e(proxima["titulo"])} &rarr;</a>')
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu"><a href="../">{e(L['titulo'])}</a> · Capítulo {r['numero']} de {len(L['capitulos'])} · {e(r['paginas'])}</span>
    <h1>{e(r['titulo'])}</h1>
    <p class="tempo-leitura">Leitura: {minutos(r)} min · Resenha</p>
    <p class="olho">{e(r['chamada'])}</p>
    <div class="barra-autor">
      <div class="mini"><img src="{rel}assets/monograma-branco.png" alt=""></div>
      <div class="quem">
        <b>Resenha de Renato W. Gomes</b>
        <span>Original: “{e(r['titulo_original'])}” — {e(L['autor'])}, {e(L['titulo'])} ({L['ano']}), {e(r['paginas'])}</span>
      </div>
    </div>
  </div>
  <div class="corpo">
{render_blocos(r['blocos'])}
{glossario_html(r.get('glossario'))}

    <div class="caixa-num">
      <div class="valor">E hoje?</div>
      <div class="exp">{e(r.get('hoje', ''))}</div>
    </div>

    <div class="fontes">
      <h3>O livro</h3>
      <ol>
        <li>{e(L['autor'])}. <b>{e(L['titulo'])}: {e(L['subtitulo'])}</b>. {e(L['local'])}: {e(L['editora'])}, {L['ano']}. Capítulo {r['numero']}, “{e(r['titulo_original'])}”, {e(r['paginas'])}.{(' ISBN ' + e(L['isbn']) + '.') if L.get('isbn') else ''} <a href="{L['compra_url']}" target="_blank" rel="noopener">Onde comprar</a>.</li>
        <li><a href="../">Todos os capítulos de {e(L['titulo'])}</a>.</li>
      </ol>
    </div>

    <p class="nota-legal">{e(nota_resenha(L))} Encontrou um erro? Escreva: a correção é publicada no próprio texto, com data.</p>

    <p class="fonte-links" style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">{' '.join(nav)}</p>
  </div>
</article>

<div class="env">
  {assine("Um capítulo novo por semana, no seu e-mail.", "A resenha em português, com a página do livro e a ponte com o debate de hoje.")}
</div>
"""
    escreve(f"leituras/{L['slug']}/{r['slug']}", cabeca(f"{r['titulo']} — {L['titulo']}, cap. {r['numero']} · Economista Renato Gomes", r["chamada"],
                                                     f"leituras/{L['slug']}/{r['slug']}/", rel, "article")
            + topo("leituras/", rel, completo=False) + corpo + rodape(rel))


# ------------------------------------------------------------------ Leituras · Documentos de época
# Obras antigas cuja tese central é conspiratória: resenha histórica (descritiva, atribuída) + "Nota do editor".
# Um JSON por volume em scripts/leituras/documentos/<slug>.json; só vai ao ar com "publicar": true.
DOC_DIR = os.path.join(LEIT_DIR, "documentos")
DOCUMENTOS = [json.load(open(os.path.join(DOC_DIR, f), encoding="utf-8")) for f in sorted(os.listdir(DOC_DIR)) if f.endswith(".json")] if os.path.isdir(DOC_DIR) else []
DOCS_PUB = [d for d in DOCUMENTOS if d.get("publicar")]


def cartao_documento(d, rel):
    return f"""    <article class="cartao">
      <a href="{rel}leituras/documentos/{d['slug']}/">
        <span class="chapeu">Documento de época · {e(d['autor'])}</span>
        <h3 class="tit tit-g">{e(d['titulo'])}</h3>
        <p class="olho">{e(d['chamada'])}</p>
        <span class="selo">Leitura: {minutos(d)} min</span>
      </a>
    </article>"""


def pagina_documento(d, anterior=None, proxima=None, destino=None):
    rel = "../../../"
    nav = []
    if anterior: nav.append(f'<a href="../{anterior["slug"]}/">&larr; {e(anterior["titulo"])}</a>')
    if proxima: nav.append(f'<a href="../{proxima["slug"]}/">{e(proxima["titulo"])} &rarr;</a>')
    nota = "".join(f"<p>{e(x)}</p>" for x in d["objecoes"])
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu">Leituras · Documentos de época · {e(d['autor'])}</span>
    <h1>{e(d['titulo'])}</h1>
    <p class="tempo-leitura">Leitura: {minutos(d)} min · Resenha histórica</p>
    <p class="olho">{e(d['chamada'])}</p>
    <div class="barra-autor">
      <div class="mini"><img src="{rel}assets/monograma-branco.png" alt=""></div>
      <div class="quem">
        <b>Resenha de Renato W. Gomes</b>
        <span>Original: “{e(d['titulo_original'])}” — {e(d['autor'])} · {e(d['volume'])} · {e(d['edicao'])}</span>
      </div>
    </div>
  </div>
  <div class="corpo">
{render_blocos(d['blocos'])}
{glossario_html(d.get('glossario'))}
{caps_documento_html(d)}
    <section class="nota-editor" id="nota-do-editor">
      <h3>Nota do editor</h3>
      {nota}
    </section>

    <p class="nota-legal">Resenha histórica: resumo e descrição do autor deste site, em suas próprias palavras, das teses de {e(d['autor'])}, a ele atribuídas. Não reproduzimos o texto da obra; as citações são curtas. A publicação desta resenha não significa endosso às teses da obra — ver a Nota do editor.</p>

    <p class="fonte-links" style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">{' '.join(nav)}</p>
  </div>
</article>
"""
    html = (cabeca(f"{d['titulo']} — Documentos de época · Economista Renato Gomes", d["chamada"], f"leituras/documentos/{d['slug']}/", rel, "article")
            + topo("leituras/", rel, completo=False) + corpo + rodape(rel))
    if destino:
        os.makedirs(os.path.dirname(destino), exist_ok=True); open(destino, "w", encoding="utf-8").write(html); return
    escreve(f"leituras/documentos/{d['slug']}", html)


def caps_documento_html(d):
    caps = d.get("capitulos") or []
    if not caps: return ""
    lis = "\n".join(f'        <li><a href="{c["slug"]}/"><b>Cap. {e(c["numero"])} · {e(c["titulo"])}</b></a> <span class="cap-meta">{e(c["paginas"])} · {minutos(c)} min</span></li>' for c in caps)
    return f'    <div class="artigos-edicao">\n      <h3>Resenhas por capítulo</h3>\n      <ol class="lista-caps" style="columns:1">\n{lis}\n      </ol>\n    </div>\n'


def pagina_doc_capitulo(d, c, anterior=None, proxima=None, destino=None):
    rel = "../../../../"
    nav = []
    if anterior: nav.append(f'<a href="../{anterior["slug"]}/">&larr; Cap. {e(anterior["numero"])} · {e(anterior["titulo"])}</a>')
    if proxima: nav.append(f'<a href="../{proxima["slug"]}/">Cap. {e(proxima["numero"])} · {e(proxima["titulo"])} &rarr;</a>')
    nota = " ".join(e(x) for x in c.get("nota", []))
    nota = nota.replace("na resenha do volume.", 'na <a href="../#nota-do-editor">resenha do volume</a>.')
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu"><a href="../">{e(d['autor'])} · {e(d['titulo_original'])} · {e(d['volume'])}</a> · Capítulo {e(c['numero'])} · {e(c['paginas'])}</span>
    <h1>{e(c['titulo'])}</h1>
    <p class="tempo-leitura">Leitura: {minutos(c)} min · Resenha histórica</p>
    <p class="olho">{e(c['chamada'])}</p>
    <div class="barra-autor">
      <div class="mini"><img src="{rel}assets/monograma-branco.png" alt=""></div>
      <div class="quem">
        <b>Resenha de Renato W. Gomes</b>
        <span>Original: “{e(c['titulo_original'])}” — {e(d['autor'])}, {e(d['titulo_original'])}, {e(d['volume'])}, {e(c['paginas'])} · {e(d['edicao'])}</span>
      </div>
    </div>
  </div>
  <div class="corpo">
{render_blocos(c['blocos'])}
{glossario_html(c.get('glossario'))}

    <section class="nota-editor nota-curta">
      <h3>Nota do editor</h3>
      <p>{nota}</p>
    </section>

    <p class="nota-legal">Resenha histórica: resumo e descrição do autor deste site, em suas próprias palavras, das teses de {e(d['autor'])}, a ele atribuídas. Não reproduzimos o texto da obra; as citações são curtas.</p>

    <p class="fonte-links" style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">{' '.join(nav)}</p>
  </div>
</article>
"""
    html = (cabeca(f"{c['titulo']} — {d['autor']}, {d['titulo_original']}, cap. {c['numero']} · Economista Renato Gomes", c["chamada"],
                   f"leituras/documentos/{d['slug']}/{c['slug']}/", rel, "article")
            + topo("leituras/", rel, completo=False) + corpo + rodape(rel))
    if destino:
        os.makedirs(os.path.dirname(destino), exist_ok=True); open(destino, "w", encoding="utf-8").write(html); return
    escreve(f"leituras/documentos/{d['slug']}/{c['slug']}", html)


def gera_documento(d, anterior=None, proxima=None, raiz_previa=None):
    """Página do volume (hub) + uma página por capítulo resenhado. raiz_previa: grava fora do fluxo normal (rascunho)."""
    dest = (os.path.join(raiz_previa, d["slug"], "index.html") if raiz_previa else None)
    pagina_documento(d, anterior, proxima, destino=dest)
    caps = d.get("capitulos") or []
    for i, c in enumerate(caps):
        dc = (os.path.join(raiz_previa, d["slug"], c["slug"], "index.html") if raiz_previa else None)
        pagina_doc_capitulo(d, c, caps[i - 1] if i > 0 else None, caps[i + 1] if i + 1 < len(caps) else None, destino=dc)


def gera_leituras():
    if not LIVROS: return
    pagina_leituras()
    for L in LIVROS:
        pagina_livro(L)
        rs = L.get("resenhas", [])
        for i, r in enumerate(rs):
            pagina_resenha(L, r, rs[i - 1] if i > 0 else None, rs[i + 1] if i + 1 < len(rs) else None)
    for i, d in enumerate(DOCS_PUB):
        gera_documento(d, DOCS_PUB[i - 1] if i > 0 else None, DOCS_PUB[i + 1] if i + 1 < len(DOCS_PUB) else None)


# ------------------------------------------------------------------ Campo Grande-MS · o livro "Campo Grande em 2036"
# Conteúdo em scripts/campo-grande/livro.json: ficha do livro e os capítulos. Página do livro em /campo-grande/,
# uma página por capítulo em /campo-grande/<slug>/. Capítulo ainda sem texto mostra o roteiro e as fontes previstas.
SITUACAO_CG = {"texto": "Texto em andamento", "dados": "Com dados", "roteiro": "Em preparação"}


def situacao_cg(c):
    s = SITUACAO_CG[c["situacao"]]
    return s + (" · tema a confirmar" if c.get("sugestao") else "")


def quadro_regiao(c):
    q = c.get("regiao")
    if not q: return ""
    lin = "\n".join(f"        <tr><td>{e(r)}</td><td>{e(q['linhas'].get(r, 'a levantar'))}</td></tr>" for r in CG["regioes"])
    nota = f'\n      <p class="regiao-nota">{e(q["nota"])}</p>' if q.get("nota") else ""
    return f"""    <section class="quadro-regiao">
      <span class="chapeu">E na sua região?</span>
      <h3>{e(q['pergunta'])}</h3>
      <div class="tabela-wrap"><table class="tabela-guia">
        <thead><tr><th>Região</th><th>{e(q['coluna'])}</th></tr></thead>
        <tbody>
{lin}
        </tbody>
      </table></div>{nota}
    </section>"""


def cartao_cg(c, rel):
    return f"""    <article class="cartao">
      <a href="{rel}campo-grande/livro/{c['slug']}/">
        <span class="chapeu">Campo Grande em 2036 · Capítulo {c['numero']}</span>
        <h3 class="tit tit-g">{e(c['titulo'])}</h3>
        <p class="olho">{e(c['chamada'])}</p>
        <span class="selo">{situacao_cg(c)}</span>
      </a>
    </article>"""


def pagina_cg_livro():
    rel = "../../"
    caps = CG["capitulos"]
    lis = "\n".join(
        f'          <li><a href="{c["slug"]}/"><b>{c["numero"]}. {e(c["titulo"])}</b></a> <span class="cap-meta">{situacao_cg(c).lower()}</span></li>'
        for c in caps)
    prontos = [c for c in caps if c["situacao"] != "roteiro"]
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu"><a href="../">Campo Grande-MS</a> · Livro · Minhas propostas para 2028</span>
    <h1>{e(CG['titulo'])}</h1>
    <p class="subtitulo-livro">{e(CG['subtitulo'])}</p>
    <p class="olho">{e(CG['chamada'])}</p>
  </div>
  <div class="corpo">
    <div class="ficha-livro">
      <h3>O livro</h3>
      <dl><dt>Autor</dt><dd>{e(CG['autor'])}</dd><dt>Capítulos</dt><dd>{len(caps)}, de cerca de 10 páginas cada</dd><dt>Situação</dt><dd>Em redação; {len(prontos)} de {len(caps)} capítulos já com texto ou dados publicados</dd></dl>
    </div>
{render_blocos(CG['blocos'])}
  </div>
</article>
<main class="env">
  <div class="faixa">
    <h2>Já dá para ler</h2>
    <span class="sub">Capítulos com texto ou dados</span>
  </div>
  <section class="grade-3">
{chr(10).join(cartao_cg(c, rel) for c in prontos)}
  </section>
  <div class="faixa">
    <h2>O livro, capítulo a capítulo</h2>
    <span class="sub">{len(caps)} capítulos</span>
  </div>
  <div class="mapa-livro">
    <section class="parte-livro">
      <ol class="lista-caps" style="columns:1">
{lis}
      </ol>
    </section>
  </div>
  {assine("Cada capítulo novo, no seu e-mail.", "O avanço do livro sobre Campo Grande, com os dados e as fontes de cada tema.")}
</main>
"""
    escreve("campo-grande/livro", cabeca("Campo Grande em 2036: Propostas — Campo Grande-MS · Economista Renato Gomes", CG["chamada"], "campo-grande/livro/", rel)
            + topo("campo-grande/", rel, completo=False) + corpo + rodape(rel))


def indice_subtopicos(c):
    sts = [b for b in c["blocos"] if b.get("tipo") == "subtopico"]
    if not sts: return ""
    li = "".join(f'<li><a href="#st-{b["numero"].replace(".", "-")}">{e(b["numero"])} {e(b["texto"])}</a></li>' for b in sts)
    return f'    <nav class="indice-st"><b>Neste capítulo</b><ul>{li}</ul></nav>\n'


def pagina_cg_capitulo(c, anterior, proxima):
    rel = "../../../"
    nav = []
    if anterior: nav.append(f'<a href="../{anterior["slug"]}/">&larr; Cap. {anterior["numero"]} · {e(anterior["titulo"])}</a>')
    if proxima: nav.append(f'<a href="../{proxima["slug"]}/">Cap. {proxima["numero"]} · {e(proxima["titulo"])} &rarr;</a>')
    aviso = ""
    if c["situacao"] == "roteiro":
        aviso = ('    <p class="aviso-cg">Capítulo em preparação. Esta página mostra o roteiro: o que o capítulo vai tratar e de onde virão os números. '
                 'O texto entra aqui quando estiver pronto.' + (" O tema deste capítulo ainda está em definição." if c.get("sugestao") else "") + '</p>\n')
    fontes = ""
    if c.get("fontes"):
        fs = "\n".join(f"        <li>{e(f)}</li>" for f in c["fontes"])
        fontes = f'    <div class="fontes">\n      <h3>Fontes deste capítulo</h3>\n      <ol>\n{fs}\n      </ol>\n    </div>\n'
    sobre = f'    <div class="caixa-leitura">\n      <h3>Sobre os dados</h3>\n      <p>{e(c["sobre_dados"])}</p>\n    </div>\n' if c.get("sobre_dados") else ""
    leitura = f' · Leitura: {minutos(c)} min' if c["situacao"] != "roteiro" else ""
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu"><a href="../">{e(CG['titulo'])}</a> · Capítulo {c['numero']} de {len(CG['capitulos'])}</span>
    <h1>{e(c['titulo'])}</h1>
    <p class="tempo-leitura situacao-cg">{situacao_cg(c)}{leitura}</p>
    <p class="olho">{e(c['chamada'])}</p>
    <div class="barra-autor">
      <div class="mini"><img src="{rel}assets/monograma-branco.png" alt=""></div>
      <div class="quem">
        <b>{e(CG['autor'])}</b>
        <span>{e(CG['titulo'])}: {e(CG['subtitulo'])} · livro em construção</span>
      </div>
    </div>
  </div>
  <div class="corpo">
{aviso}{indice_subtopicos(c)}{render_blocos(c['blocos'])}
{quadro_regiao(c)}
{glossario_html(c.get('glossario'))}
{sobre}{fontes}
    <p class="nota-legal">Texto em construção, sujeito a revisão. Encontrou um erro ou tem um dado da sua região? Escreva: a correção é publicada no próprio texto, com data.</p>

    <p class="fonte-links" style="display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap">{' '.join(nav)}</p>
  </div>
</article>

<div class="env">
  {assine("Cada capítulo novo, no seu e-mail.", "O avanço do livro sobre Campo Grande, com os dados e as fontes de cada tema.")}
</div>
"""
    escreve(f"campo-grande/livro/{c['slug']}", cabeca(f"{c['titulo']} — Campo Grande em 2036, cap. {c['numero']} · Economista Renato Gomes", c["chamada"],
                                               f"campo-grande/livro/{c['slug']}/", rel, "article")
            + topo("campo-grande/", rel, completo=False) + corpo + rodape(rel))


def pagina_cg_hub():
    rel = "../"
    cards = "\n".join(f"""    <article class="cartao colecao">
      <a href="{sl}/">
        <span class="chapeu">Campo Grande-MS</span>
        <h3 class="tit tit-g">{e(nm)}</h3>
        <p class="olho">{e(ds)}</p>
      </a>
    </article>""" for sl, nm, ds in SUB_CG)
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:40px auto 10px">
    <span class="chapeu">Campo Grande-MS</span>
    <h1>Campo Grande, com documento na mesa</h1>
    <p class="olho">A capital de Mato Grosso do Sul vista pelo economista: o livro com as propostas para a cidade, o retrato de como ela está hoje e as notícias que importam, sempre com a fonte.</p>
  </div>
  <section class="grade-3">
{cards}
  </section>
  {assine("Campo Grande no seu e-mail.", "Cada capítulo novo do livro, os dados atualizados e as notícias que importam para a cidade.")}
</main>
"""
    escreve("campo-grande", cabeca("Campo Grande-MS — Economista Renato Gomes", "Campo Grande vista pelo economista: o livro com as propostas, a situação atual da cidade e as notícias importantes, com fonte.", "campo-grande/", rel)
            + topo("campo-grande/", rel, completo=False) + corpo + rodape(rel))


def pagina_cg_situacao():
    rel = "../../"
    linhas = []
    for c in CG["capitulos"]:
        ind = c.get("indicador")
        if c["numero"] == 1 or c["slug"] == "consideracoes-finais": continue
        if ind:
            linhas.append(f'        <tr><td><a href="../livro/{c["slug"]}/">{e(c["titulo"])}</a></td><td><b>{e(ind["valor"])}</b> {e(ind["texto"])}</td><td>{e(ind["fonte"])}</td></tr>')
        else:
            linhas.append(f'        <tr><td><a href="../livro/{c["slug"]}/">{e(c["titulo"])}</a></td><td class="cap-futuro">Dado em levantamento</td><td class="cap-futuro">{e(c.get("fonte_prevista", "—"))}</td></tr>')
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu"><a href="../">Campo Grande-MS</a> · Situação atual</span>
    <h1>Como Campo Grande está hoje</h1>
    <p class="olho">O retrato da cidade tema a tema, com o número mais recente conferido e a fonte. Quando o dado ainda não foi levantado, a tabela diz isso, em vez de estimar.</p>
  </div>
  <div class="corpo">
    <div class="tabela-wrap"><table class="tabela-guia tabela-situacao">
      <caption>Campo Grande, tema a tema</caption>
      <thead><tr><th>Tema</th><th>O que se sabe hoje</th><th>Fonte</th></tr></thead>
      <tbody>
{chr(10).join(linhas)}
      </tbody>
    </table></div>
    <p>Cada tema leva ao capítulo correspondente do livro, onde o dado aparece com a divisão pelas sete regiões urbanas: Centro, Segredo, Prosa, Bandeira, Anhanduizinho, Lagoa e Imbirussu.</p>
    <p class="nota-legal">A tabela é atualizada à medida que cada dado é conferido no documento original. Correções são publicadas no próprio texto, com data.</p>
  </div>
</article>
<div class="env">
  {assine("Campo Grande no seu e-mail.", "Cada capítulo novo do livro, os dados atualizados e as notícias que importam para a cidade.")}
</div>
"""
    escreve("campo-grande/situacao-atual", cabeca("Situação atual — Campo Grande-MS · Economista Renato Gomes", "Como Campo Grande está hoje, tema a tema, com o número e a fonte de cada dado.", "campo-grande/situacao-atual/", rel)
            + topo("campo-grande/", rel, completo=False) + corpo + rodape(rel))


def pagina_cg_noticias():
    rel = "../../"
    if NOTICIAS_CG:
        itens = "\n".join(f"""    <article class="noticia-cg">
      <span class="chapeu">{e(n['data'])} · {e(n.get('tema', ''))}</span>
      <h2>{e(n['titulo'])}</h2>
      <p>{e(n['comentario'])}</p>
      <p class="fonte-links">Fonte: <a href="{e(n['fonte_url'])}" target="_blank" rel="noopener">{e(n['fonte'])}</a></p>
    </article>""" for n in sorted(NOTICIAS_CG, key=lambda n: n["data_iso"], reverse=True))
    else:
        itens = '    <p class="aviso-cg">Ainda não há notícias publicadas nesta seção. As primeiras entram em breve.</p>'
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu"><a href="../">Campo Grande-MS</a> · Notícias importantes</span>
    <h1>Notícias importantes</h1>
    <p class="olho">Os fatos que mexem com a vida da cidade (orçamento, obras, serviços, emprego), cada um com a fonte original e um comentário curto do economista.</p>
  </div>
  <div class="corpo">
{itens}
  </div>
</article>
<div class="env">
  {assine("Campo Grande no seu e-mail.", "Cada capítulo novo do livro, os dados atualizados e as notícias que importam para a cidade.")}
</div>
"""
    escreve("campo-grande/noticias", cabeca("Notícias importantes — Campo Grande-MS · Economista Renato Gomes", "Os fatos que mexem com Campo Grande, com a fonte e um comentário curto.", "campo-grande/noticias/", rel)
            + topo("campo-grande/", rel, completo=False) + corpo + rodape(rel))


def gera_campo_grande():
    if not CG: return
    pagina_cg_hub(); pagina_cg_livro(); pagina_cg_situacao(); pagina_cg_noticias()
    cs = CG["capitulos"]
    for i, c in enumerate(cs):
        pagina_cg_capitulo(c, cs[i - 1] if i > 0 else None, cs[i + 1] if i + 1 < len(cs) else None)



def sitemap():
    urls = ["", "tech/", "bitcoin/", "historia/", "economia/", "ms/", "arquivo/", "sobre/"] + [f"arquivo/{c['id']}/" for c in COLECOES] + [f"arquivo/eua/{s_['slug']}/" for s_ in SERIES_AEA] + ["ensaios/"] + [f"arquivo/{ed['slug']}/" for ed in DADOS["edicoes"]] + [f"arquivo/{ed['slug']}/{c['slug']}/" for ed in DADOS["edicoes"] for c in ed.get("comentarios", [])]
    if LIVROS:
        urls += ["leituras/"]
        for L in LIVROS:
            urls += [f"leituras/{L['slug']}/"] + [f"leituras/{L['slug']}/{r['slug']}/" for r in L.get("resenhas", [])]
        for d in DOCS_PUB:
            urls += [f"leituras/documentos/{d['slug']}/"] + [f"leituras/documentos/{d['slug']}/{c['slug']}/" for c in d.get("capitulos", [])]
    if NOTAS: urls += ["notas/"] + [f"notas/{n['slug']}/" for n in NOTAS]
    if CG: urls += ["campo-grande/"] + [f"campo-grande/{sl}/" for sl, _, _ in SUB_CG] + [f"campo-grande/livro/{c['slug']}/" for c in CG["capitulos"]]
    hoje = date.today().isoformat()
    x = "\n".join(f"  <url><loc>{DOMINIO}/{u}</loc><lastmod>{hoje}</lastmod></url>" for u in urls)
    open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{x}\n</urlset>\n')
    print("ok site/sitemap.xml")


if __name__ == "__main__":
    pagina_inicio(); pagina_arquivo(); [pagina_colecao(c) for c in COLECOES]; pagina_ensaios(); pagina_analises(); pagina_tech(); pagina_bitcoin(); pagina_historia(); pagina_economia(); pagina_ms(); redireciona("servicos", "tech/"); pagina_sobre(); pagina_obrigado()
    if NOTAS:
        pagina_notas()
        for n in NOTAS: pagina_nota(n)
    for c_ in COLECOES:
        if c_["id"] == "eua":
            for s_ in SERIES_AEA: pagina_serie(c_, s_)
    principais = [ed for ed in DADOS["edicoes"] if not str(ed["numero"]).startswith("ES")]
    es = sorted([ed for ed in DADOS["edicoes"] if str(ed["numero"]).startswith("ES")], key=lambda x: int(str(x["numero"])[2:]))
    for grupo in (principais, es):
        for i, ed in enumerate(grupo):
            pagina_edicao(ed, grupo[i - 1] if i > 0 else None, grupo[i + 1] if i + 1 < len(grupo) else None)
    for ed in DADOS["edicoes"]:
        cs = ed.get("comentarios") or []
        for k, c in enumerate(cs):
            pagina_comentario(ed, c, cs[k - 1] if k > 0 else None, cs[k + 1] if k + 1 < len(cs) else None)
    gera_leituras()
    gera_campo_grande()
    sitemap()
