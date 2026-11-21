"""Gera o site inteiro (páginas estáticas) a partir de scripts/arquivo/edicoes.json.

Uso:  python scripts/gera_site.py
Saída: site/index.html, site/arquivo/, site/analises/, site/servicos/, site/sobre/, site/obrigado/,
       site/sitemap.xml
Cabeçalho, menu e rodapé ficam aqui, num lugar só: mexeu aqui, mudou em todas as páginas.
"""
import json, re, os, html
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(RAIZ, "site")
DADOS = json.load(open(os.path.join(RAIZ, "scripts", "arquivo", "edicoes.json"), encoding="utf-8"))
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
CSS_V = "20261121a"
LEMA = "Economia pelas fontes"
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

# Menu principal: poucas seções, nomes curtos. Item novo aqui aparece em todas as páginas.
MENU = [("", "Início"), ("arquivo/", "Arquivo"), ("leituras/", "Leituras"), ("ensaios/", "Ensaios"),
        ("analises/", "Análises"), ("campo-grande/", "Campo Grande"), ("servicos/", "Serviços"), ("sobre/", "Sobre")]


def topo(ativo, rel, completo=True):
    """Barra única no alto, no modelo das newsletters de opinião: marca à esquerda, seções curtas
    no meio e o botão de assinar sempre visível à direita. `completo` ficou por compatibilidade:
    a apresentação longa agora mora só na página inicial."""
    itens = []
    for h, n in MENU:
        cls = ' class="ativo"' if h == ativo else ""
        if h == "arquivo/":
            subs = "".join(f'<li><a href="{rel}arquivo/{c["id"]}/">{e(c["regiao"])}</a></li>' for c in COLECOES)
            itens.append(f'<li class="tem-sub"><a href="{rel}{h}"{cls}>{n}</a>'
                         f'<button class="sub-toggle" type="button" aria-expanded="false" aria-label="Abrir as regiões do Arquivo">&#9662;</button>'
                         f'<ul class="sub"><li><a href="{rel}arquivo/">Todas as coleções</a></li>{subs}</ul></li>')
        elif h == "campo-grande/" and CG:
            subs = "".join(f'<li><a href="{rel}campo-grande/{sl}/">{e(nm)}</a></li>' for sl, nm, _ in SUB_CG)
            itens.append(f'<li class="tem-sub"><a href="{rel}{h}"{cls}>{n}</a>'
                         f'<button class="sub-toggle" type="button" aria-expanded="false" aria-label="Abrir as seções de Campo Grande-MS">&#9662;</button>'
                         f'<ul class="sub sub-larga">{subs}</ul></li>')
        else:
            itens.append(f'<li><a href="{rel}{h}"{cls}>{n}</a></li>')
    itens.append(f'<li class="menu-extra"><a href="{rel}notas/">Notas · Então × Agora</a></li>')
    nav = "\n        ".join(itens)
    return f"""<header class="barra">
  <div class="env barra-in">
    <a class="marca-lockup compacta" href="{rel}" aria-label="Economista Renato Gomes, página inicial">{LOGO}<span class="marca-nome"><span>Economista</span><span>Renato Gomes</span></span></a>
    <nav class="secoes" aria-label="Menu principal">
      <ul class="menu" id="menu-principal">
        {nav}
      </ul>
    </nav>
    <div class="barra-acoes">
      <a class="ig" href="https://instagram.com/economistarenato" target="_blank" rel="noopener" aria-label="Instagram @economistarenato" title="@economistarenato">{IG_SVG}</a>
      <a class="botao botao-cheio botao-assinar" href="#assine">Assinar</a>
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="menu-principal" aria-label="Abrir o menu"><span aria-hidden="true">&#9776;</span></button>
    </div>
  </div>
</header>
<script>
document.querySelector('.nav-toggle').addEventListener('click',function(){{var m=document.getElementById('menu-principal');var o=m.classList.toggle('aberto');this.setAttribute('aria-expanded',o)}});
document.querySelectorAll('.sub-toggle').forEach(function(b){{b.addEventListener('click',function(){{var li=b.parentNode;var o=li.classList.toggle('sub-aberto');b.setAttribute('aria-expanded',o)}})}});
</script>
"""


def assine(titulo="A carta do economista, no seu e-mail.", texto="Um clássico comentado e uma análise com fonte primária, uma vez por semana. Sem custo e sem spam."):
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
<footer>
  <div class="env">
    <div class="rodape-grade">
      <div class="rodape-marca">
        <a class="marca-lockup compacta" href="{rel}">{LOGO}<span class="marca-nome"><span>Economista</span><span>Renato Gomes</span></span></a>
        <p class="rodape-texto">{LEMA}. Análise econômica independente: toda afirmação numérica publicada aqui traz a fonte primária — documento histórico, orçamento, Diário Oficial, IBGE ou órgão de controle.</p>
      </div>
      <div>
        <h4>Conteúdo</h4>
        <ul>
          <li><a href="{rel}arquivo/">Arquivo · Clássicos comentados</a></li>
          <li><a href="{rel}arquivo/eua/">— Estados Unidos</a></li>
          <li><a href="{rel}arquivo/europa/">— Europa</a></li>
          <li><a href="{rel}arquivo/china/">— China</a></li>
          <li><a href="{rel}leituras/">Leituras · Livros comentados</a></li>
          <li><a href="{rel}campo-grande/">Campo Grande-MS</a></li>
          <li><a href="{rel}ensaios/">Ensaios</a></li>
          <li><a href="{rel}notas/">Notas · Então × Agora</a></li>
          <li><a href="{rel}analises/">Análises</a></li>
        </ul>
      </div>
      <div>
        <h4>Trabalho</h4>
        <ul>
          <li><a href="{rel}servicos/">Consultoria</a></li>
          <li><a href="{rel}servicos/#palestras">Palestras e cursos</a></li>
          <li><a href="{rel}servicos/#contato">Contato</a></li>
          <li><a href="#assine">Newsletter</a></li>
        </ul>
      </div>
      <div>
        <h4>Sobre</h4>
        <ul>
          <li><a href="{rel}sobre/">Quem sou</a></li>
          <li><a href="{rel}sobre/#metodo">Como eu apuro os números</a></li>
          <li><a href="https://instagram.com/economistarenato" target="_blank" rel="noopener">@economistarenato</a></li>
        </ul>
      </div>
    </div>
    <div class="rodape-fim">
      <span>© {date.today().year} Renato W. Gomes · Economista, CORECON-MS 1297</span>
      <span>Conteúdo de análise e opinião pessoal. Correções são publicadas no próprio texto, com data.</span>
    </div>
    <p class="rodape-fontes">Documentos históricos do Arquivo: domínio público, via JSTOR Early Journal Content e Internet Archive, sempre com a fonte indicada. Este site não tem afiliação com as instituições que publicaram os periódicos originais.</p>
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
def num_int(ed):
    n = str(ed.get("numero", ""))
    return int(n) if n.isdigit() else -1


def recentes():
    """Edições da numeração geral, da mais nova para a mais antiga (a última publicada vem primeiro)."""
    return sorted([ed for ed in DADOS["edicoes"] if num_int(ed) > 0], key=num_int, reverse=True)


def capa_de(nome, rel):
    """Imagem da peça (fac-símile do original) se existir em assets/arquivo/."""
    return f"{rel}assets/arquivo/{nome}.jpg" if os.path.exists(os.path.join(SITE, "assets", "arquivo", f"{nome}.jpg")) else ""


def meta_item(ed, extra=""):
    curto = e((serie_de(ed) or {}).get("curto", ""))
    partes = [p for p in (rotulo_num(ed), curto, e(ed["data"]), extra) if p]
    return " · ".join(partes)


def item_lista(ed, rel):
    img = capa_de(ed["slug"], rel)
    mini = f'<img class="item-mini" src="{img}" alt="" loading="lazy">' if img else ""
    return f"""      <li class="item">
        <a href="{rel}arquivo/{ed['slug']}/">
          <div class="item-txt">
            <h3 class="item-tit">{e(ed['titulo'])}</h3>
            <p class="item-olho">{e(ed['chamada'])}</p>
            <span class="item-meta">{meta_item(ed, f'{minutos(ed)} min')}</span>
          </div>
          {mini}
        </a>
      </li>"""


def pagina_inicio():
    rel = ""
    eds = recentes()
    dest = eds[0]
    img = capa_de(dest["slug"], rel)
    fig = f'<img src="{img}" alt="Fac-símile do original: {e(dest.get("titulo_original", dest["titulo"]))}">' if img else ""
    # ao lado do destaque: os artigos comentados da mesma edição ("nesta edição")
    lado = []
    for c in dest.get("comentarios", [])[:5]:
        ci = capa_de(f"{dest['slug']}--{c['slug']}", rel)
        mini = f'<img class="item-mini" src="{ci}" alt="" loading="lazy">' if ci else ""
        lado.append(f"""        <li class="item item-curto">
          <a href="{rel}arquivo/{dest['slug']}/{c['slug']}/">
            <div class="item-txt">
              <h3 class="item-tit">{e(c['titulo'])}</h3>
              <span class="item-meta">{e(c.get('autores', ''))} · {minutos(c)} min</span>
            </div>
            {mini}
          </a>
        </li>""")
    lado_html = ""
    if lado:
        lado_html = f"""    <aside class="vitrine-lado">
      <div class="rotulo-sec">Nesta edição</div>
      <ul class="lista-itens">
{chr(10).join(lado)}
      </ul>
    </aside>"""
    lista = "\n".join(item_lista(ed, rel) for ed in eds[1:11])
    series = []
    for s_ in SERIES_AEA:
        n = sum(1 for ed in DADOS["edicoes"] if serie_de(ed) is s_)
        if n:
            series.append(f'<li><a href="{rel}arquivo/eua/{s_["slug"]}/"><b>{e(s_["curto"])}</b><span>{s_["periodo"]} · {n} {"edição" if n == 1 else "edições"}</span></a></li>')
    series.append(f'<li><a href="{rel}leituras/"><b>Leituras</b><span>Livros clássicos comentados, capítulo a capítulo</span></a></li>')
    if CG:
        series.append(f'<li><a href="{rel}campo-grande/"><b>Campo Grande-MS</b><span>A cidade com o número e a fonte de cada dado</span></a></li>')
    series_html = "\n          ".join(series)
    corpo = f"""
<main>

  <section class="boas-vindas">
    <div class="env">
      <span class="bv-chapeu">{LEMA}</span>
      <h1 class="bv-tit">O que os documentos dizem, antes da opinião.</h1>
      <p class="bv-texto">Clássicos e debates da economia lidos no original e comentados em português, e as contas públicas de hoje com o documento oficial no rodapé. Por <b>Renato W. Gomes</b>, economista (CORECON-MS 1297).</p>
      <form class="form-linha bv-form" name="assinantes" method="POST" data-netlify="true" action="/obrigado/">
        <input type="hidden" name="form-name" value="assinantes">
        <input type="email" name="email" placeholder="seu@email.com.br" aria-label="Seu e-mail" required>
        <button class="botao botao-cheio" type="submit">Assinar</button>
      </form>
      <p class="bv-nota">Uma carta por semana, sem custo. Você sai quando quiser.</p>
    </div>
  </section>

  <section class="env vitrine{' vitrine-so' if not lado else ''}">
    <article class="destaque">
      <a href="{rel}arquivo/{dest['slug']}/">
        <figure class="destaque-fig">{fig}</figure>
        <span class="chapeu">Mais recente · {meta_item(dest)}</span>
        <h2 class="destaque-tit">{e(dest['titulo'])}</h2>
        <p class="destaque-olho">{e(dest['chamada'])}</p>
        <span class="item-meta">Renato W. Gomes · {minutos(dest)} min de leitura</span>
      </a>
    </article>
{lado_html}
  </section>

  <div class="env dupla">
    <section class="recentes">
      <div class="abas" role="navigation" aria-label="Atalhos">
        <span class="aba ativa">Mais recentes</span>
        <a class="aba" href="{rel}ensaios/">Ensaios</a>
        <a class="aba" href="{rel}arquivo/">Arquivo completo</a>
      </div>
      <ul class="lista-itens">
{lista}
      </ul>
      <a class="ver-mais" href="{rel}arquivo/eua/">Ver todas as edições &rarr;</a>
    </section>

    <aside class="lateral">
      <div class="rotulo-sec">Séries</div>
      <ul class="lista-series">
          {series_html}
      </ul>

      <div class="rotulo-sec">A regra da casa</div>
      <p class="lateral-txt">Nenhuma afirmação numérica sem fonte primária citada. Quando o dado não existe, o texto diz que não existe. Erro se corrige no próprio texto, com data.</p>

      <div class="rotulo-sec">Quem escreve</div>
      <div class="autor-mini">
        <img src="{rel}assets/retrato-palacios.jpg" alt="Renato W. Gomes">
        <p class="lateral-txt">Economista há 15 anos, consultor independente, especialização em finanças pela FGV. <a href="{rel}sobre/">Trajetória e método &rarr;</a></p>
      </div>
      <a class="botao lateral-botao" href="{rel}servicos/">Consultoria e palestras</a>
    </aside>
  </div>

  <div class="env">
  {assine()}
  </div>

</main>
"""
    escreve("", cabeca(f"Economista Renato Gomes — {LEMA}", "Economia pelas fontes: clássicos comentados, contas públicas com documento oficial e consultoria. Por Renato W. Gomes, economista (CORECON-MS 1297).", "", rel)
            + topo("", rel) + corpo + rodape(rel))



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
    ultimas = "\n".join(cartao_edicao(ed, rel) for ed in [x for x in recentes() if x.get("colecao", "eua") == "eua"][:3])
    corpo = f"""
<main class="env">
{subnav_arquivo("", "")}
  <div class="artigo-topo" style="max-width:820px;margin:28px auto 10px">
    <span class="chapeu">Arquivo · Clássicos comentados</span>
    <h1>Os debates que criaram a economia moderna</h1>
    <p class="olho">Um periódico de referência por região, lido no original e explicado em português — com o documento sempre a um clique e a pergunta de hoje no fim de cada texto.</p>
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
{ultimas}
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
            + topo("notas/", rel, completo=False) + corpo + rodape(rel))


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
            + topo("notas/", rel, completo=False) + corpo + rodape(rel))


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
            + topo("ensaios/", rel, completo=False) + corpo + rodape(rel))


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


def pagina_servicos():
    rel = "../"
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:40px auto 10px">
    <span class="chapeu opiniao">Serviços</span>
    <h1>Consultoria, palestras e cursos</h1>
    <p class="olho">O mesmo método das análises — documento, número e fonte — aplicado ao seu negócio ou ao seu evento.</p>
  </div>

  <section class="grade-3">
    <article class="cartao produto">
      <span class="chapeu">Consultoria</span>
      <h3 class="tit tit-g">Planejamento financeiro e tributário</h3>
      <p class="olho">Planejamento contábil, tributário e financeiro para empresas, com o mesmo método das análises: documento, número e fonte.</p>
    </article>
    <article class="cartao produto" id="palestras">
      <span class="chapeu dado">Palestras</span>
      <h3 class="tit tit-g">Economia para quem decide</h3>
      <p class="olho">Finanças públicas, leitura de orçamento e história econômica aplicada: o que os debates de 1886 a 1922 ensinam sobre monopólios, concessões e regulação hoje.</p>
    </article>
    <article class="cartao produto">
      <span class="chapeu opiniao">Cursos</span>
      <h3 class="tit tit-g">Economia pelas fontes</h3>
      <p class="olho">Cursos curtos sobre como ler um orçamento público e sobre os clássicos da economia lidos no original.</p>
      <span class="selo">Em preparação</span>
    </article>
  </section>

  <div class="faixa" id="contato">
    <h2>Contato</h2>
    <span class="sub">Conte o que você precisa</span>
  </div>
  <section class="assine">
    <div>
      <h3>Fale comigo.</h3>
      <p>Consultoria, palestra ou curso: descreva em poucas linhas e eu respondo por e-mail. Também pelo Instagram <a href="https://instagram.com/economistarenato" target="_blank" rel="noopener">@economistarenato</a>.</p>
    </div>
    <div>
      <form class="form-contato" name="contato" method="POST" data-netlify="true" action="/obrigado/">
        <input type="hidden" name="form-name" value="contato">
        <input type="text" name="nome" placeholder="Seu nome" aria-label="Seu nome" required>
        <input type="email" name="email" placeholder="seu@email.com.br" aria-label="Seu e-mail" required>
        <select name="assunto" aria-label="Assunto"><option>Consultoria</option><option>Palestra</option><option>Curso</option><option>Outro</option></select>
        <textarea name="mensagem" rows="4" placeholder="Em poucas linhas, o que você precisa" aria-label="Mensagem" required></textarea>
        <button class="botao botao-cheio" type="submit">Enviar</button>
      </form>
    </div>
  </section>
</main>
"""
    escreve("servicos", cabeca("Serviços — Economista Renato Gomes", "Consultoria em planejamento financeiro e tributário, palestras e cursos de economia e finanças públicas.", "servicos/", rel)
            + topo("servicos/", rel, completo=False) + corpo + rodape(rel))


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
    <p class="olho">Sua mensagem chegou. Se foi a assinatura da carta, a próxima edição vai direto para o seu e-mail; se foi um contato, eu respondo em breve.</p>
    <p><a class="botao botao-cheio" href="../">Voltar ao início</a> <a class="botao" href="../arquivo/">Ler o arquivo</a></p>
  </div>
</main>
"""
    escreve("obrigado", cabeca("Obrigado — Economista Renato Gomes", "Mensagem recebida.", "obrigado/", rel) + topo("", rel, completo=False) + corpo + rodape(rel))


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
    urls = ["", "arquivo/", "analises/", "servicos/", "sobre/"] + [f"arquivo/{c['id']}/" for c in COLECOES] + [f"arquivo/eua/{s_['slug']}/" for s_ in SERIES_AEA] + ["ensaios/"] + [f"arquivo/{ed['slug']}/" for ed in DADOS["edicoes"]] + [f"arquivo/{ed['slug']}/{c['slug']}/" for ed in DADOS["edicoes"] for c in ed.get("comentarios", [])]
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
    pagina_inicio(); pagina_arquivo(); [pagina_colecao(c) for c in COLECOES]; pagina_ensaios(); pagina_analises(); pagina_servicos(); pagina_sobre(); pagina_obrigado()
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
