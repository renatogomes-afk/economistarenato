"""Gera o site inteiro (páginas estáticas) a partir de scripts/arquivo/edicoes.json.

Uso:  python scripts/gera_site.py
Saída: site/index.html, site/arquivo/, site/analises/, site/servicos/, site/sobre/, site/obrigado/,
       site/sitemap.xml
Cabeçalho, menu e rodapé ficam aqui, num lugar só: mexeu aqui, mudou em todas as páginas.
"""
import json, os, html
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(RAIZ, "site")
DADOS = json.load(open(os.path.join(RAIZ, "scripts", "arquivo", "edicoes.json"), encoding="utf-8"))
LOGO = open(os.path.join(RAIZ, "scripts", "arquivo", "_logo.svg"), encoding="utf-8").read().strip()
DOMINIO = "https://economistarenato.com.br"
CSS_V = "20261108a"
LEMA = "Economia pelas fontes"
SUBLEMA = "Análise econômica com documento na mesa — dos clássicos às contas públicas de hoje"

MENU = [("", "Início"), ("arquivo/", "Arquivo"), ("analises/", "Análises"), ("servicos/", "Serviços"), ("sobre/", "Sobre")]
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


def topo(ativo, rel, completo=True):
    nav = "\n".join(f'      <a href="{rel}{h}"{" class=\"ativo\"" if h == ativo else ""}>{n}</a>' for h, n in MENU)
    nav += '\n      <a href="https://instagram.com/economistarenato" target="_blank" rel="noopener">@economistarenato</a>'
    if completo:
        cab = f"""  <div class="env">
    <div class="cabecalho">
      <a class="marca-lockup" href="{rel}">{LOGO}<span class="marca-nome"><span>Economista</span><span>Renato Gomes</span></span></a>
      <div class="lema"><b>{LEMA}.</b> {SUBLEMA}</div>
      <div class="canto">
        <a class="botao" href="{rel}servicos/">Consultoria</a>
        <a class="botao botao-cheio" href="#assine">Assinar</a>
      </div>
    </div>
  </div>"""
    else:
        cab = f"""  <div class="env">
    <div class="cabecalho" style="padding:18px 0 14px">
      <a class="marca-lockup compacta" href="{rel}">{LOGO}<span class="marca-nome"><span>Economista</span><span>Renato Gomes</span></span></a>
      <div class="canto">
        <a class="botao botao-cheio" href="#assine">Assinar</a>
      </div>
    </div>
  </div>"""
    return f"""<header>
{cab}
  <nav class="secoes">
    <div class="env">
{nav}
    </div>
  </nav>
</header>
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
          <li><a href="{rel}analises/">Análises</a></li>
          <li><a href="{rel}#assine">A carta do economista</a></li>
        </ul>
      </div>
      <div>
        <h4>Trabalho</h4>
        <ul>
          <li><a href="{rel}servicos/">Consultoria</a></li>
          <li><a href="{rel}servicos/#palestras">Palestras e cursos</a></li>
          <li><a href="{rel}servicos/#contato">Contato</a></li>
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
      <span>© {date.today().year} Renato W. Gomes · Economista, CORECON-MS 1297 · Campo Grande, MS</span>
      <span>Conteúdo de análise e opinião pessoal. Correções são publicadas no próprio texto, com data.</span>
    </div>
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
        <span class="chapeu">Arquivo · Nº {ed['numero']} · {e(ed['data'])}</span>
        <h3 class="tit tit-g">{e(ed['titulo'])}</h3>
        <p class="olho">{e(ed['chamada'])}</p>
        <span class="selo">{e(ed['titulo_original'])}</span>
      </a>
    </article>"""


# ------------------------------------------------------------------ páginas
def pagina_inicio():
    rel = ""
    eds = DADOS["edicoes"]
    cartoes = "\n".join(cartao_edicao(ed, rel) for ed in eds[:3])
    corpo = f"""
<main class="env">

  <section class="capa capa-dupla">
    <article class="manchete">
      <span class="chapeu opiniao">{LEMA}</span>
      <h1 class="tit tit-xl">O que os documentos dizem — antes da opinião.</h1>
      <p class="olho olho-xl">Este é o espaço de Renato W. Gomes, economista. Aqui se lê a economia pelas fontes: os clássicos e os debates que formaram a disciplina, lidos no original e explicados em português, e as contas públicas de hoje, sempre com o documento no rodapé.</p>
      <div class="assin"><span>Por <b>Renato W. Gomes</b></span><i class="ponto"></i><span>Economista · CORECON-MS 1297</span></div>
      <figure style="margin-top:20px">
        <img src="assets/entrevista-palacios.jpg" alt="Renato W. Gomes em entrevista" style="aspect-ratio:16/9;object-fit:cover">
        <figcaption><b>Renato W. Gomes</b>, economista, em entrevista. <span class="credito">Foto: Miguel Palacios</span></figcaption>
      </figure>
    </article>

    <aside class="trilho">
      <div class="trilho-tit">A série em curso</div>
      <div class="trilho-num">1886–1922</div>
      <p class="olho" style="margin-top:6px">As publicações da American Economic Association: monopólios, ferrovias, moeda, trabalho e o papel do Estado, discutidos por quem viveu a primeira grande era dos trustes.</p>
      <a class="botao botao-cheio" href="arquivo/" style="display:inline-block;margin-top:12px">Abrir o arquivo</a>

      <div class="trilho-tit" style="margin-top:30px">A regra da casa</div>
      <p class="olho" style="margin-top:0">Nenhuma afirmação numérica sem fonte primária citada. Quando o dado não existe, o texto diz que não existe. Erro se corrige no próprio texto, com data.</p>
    </aside>
  </section>

  <div class="faixa" id="arquivo">
    <h2>Arquivo · Clássicos comentados</h2>
    <span class="sub">Os debates que criaram a economia moderna, edição por edição</span>
    <a class="mais" href="arquivo/">Ver o arquivo &rarr;</a>
  </div>
  <section class="grade-3">
{cartoes}
  </section>

  <div class="faixa" id="trabalho">
    <h2>O que se publica aqui</h2>
    <span class="sub">E o que vem a seguir</span>
  </div>
  <section class="grade-3">
    <article class="cartao produto">
      <span class="chapeu">Arquivo</span>
      <h3 class="tit tit-g">Clássicos comentados</h3>
      <p class="olho">Uma edição ou obra por semana: resumo em português, o documento original e a ponte com o debate de hoje.</p>
      <span class="selo">Semanal</span>
    </article>
    <article class="cartao produto">
      <span class="chapeu dado">Análises</span>
      <h3 class="tit tit-g">Contas públicas com fonte</h3>
      <p class="olho">Orçamento, arrecadação, renúncia fiscal e investimento — lidos no documento oficial e explicados em linguagem de gente.</p>
      <span class="selo">Em preparação</span>
    </article>
    <article class="cartao produto">
      <span class="chapeu opiniao">Serviços</span>
      <h3 class="tit tit-g">Consultoria e palestras</h3>
      <p class="olho">Planejamento financeiro e tributário para empresas, e palestras sobre economia, finanças públicas e história econômica.</p>
      <a class="selo" href="servicos/">Conheça &rarr;</a>
    </article>
  </section>

  <div class="faixa" id="sobre">
    <h2>Quem escreve</h2>
    <span class="sub">E com que método</span>
    <a class="mais" href="sobre/">Página completa &rarr;</a>
  </div>
  <section class="coluna-destaque">
    <div class="retrato"><img src="assets/retrato-palacios.jpg" alt="Renato W. Gomes" style="width:100%;height:100%;object-fit:cover;border-radius:50%"></div>
    <div>
      <h3 class="tit tit-g" style="font-style:normal">Renato W. Gomes</h3>
      <p class="olho olho-xl">Economista há 15 anos, consultor independente com especialização em finanças pela Fundação Getúlio Vargas. Atendeu mais de 300 empresas em planejamento contábil, tributário e financeiro, e trabalhou no mercado financeiro no Rio de Janeiro e em Brasília.</p>
      <p class="olho">O método é o mesmo para um relatório de 1886 e para o orçamento de 2026: ler o documento original, citar a fonte e separar o que é fato do que é opinião.</p>
      <div class="assin"><a href="sobre/"><b>Leia o método completo</b></a><i class="ponto"></i><a href="https://instagram.com/economistarenato" target="_blank" rel="noopener">@economistarenato</a></div>
    </div>
  </section>

  {assine()}

</main>
"""
    escreve("", cabeca(f"Economista Renato Gomes — {LEMA}", "Economia pelas fontes: clássicos comentados, contas públicas com documento oficial e consultoria. Por Renato W. Gomes, economista (CORECON-MS 1297).", "", rel)
            + topo("", rel) + corpo + rodape(rel))


def pagina_arquivo():
    rel = "../"
    s = DADOS["serie"]; eds = DADOS["edicoes"]
    cartoes = "\n".join(cartao_edicao(ed, rel) for ed in eds)
    prox = "\n".join(f"          <li>{e(p)}</li>" for p in DADOS["proximas"])
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:40px auto 10px">
    <span class="chapeu">Arquivo · Clássicos comentados</span>
    <h1>Os debates que criaram a economia moderna</h1>
    <p class="olho">Obras e periódicos de domínio público lidos no original e explicados em português — com o documento sempre a um clique e a pergunta de hoje no fim de cada texto.</p>
  </div>

  <div class="faixa">
    <h2>Série 1 · {e(s['titulo'])}</h2>
    <span class="sub">{len(eds)} edições publicadas</span>
  </div>
  <p class="olho" style="max-width:820px">{e(s['descricao'])}</p>
  <section class="grade-3">
{cartoes}
  </section>

  <div class="faixa">
    <h2>Próximas edições</h2>
    <span class="sub">Na ordem de publicação</span>
  </div>
  <div class="corpo" style="max-width:820px;margin:0">
    <ul>
{prox}
    </ul>
    <p class="nota-legal">Fontes: publicações da American Economic Association (1886–1922), em domínio público, via JSTOR Early Journal Content e Internet Archive. Os resumos e comentários são do autor deste site, que não tem afiliação com a American Economic Association.</p>
  </div>

  {assine("Uma edição comentada por semana, no seu e-mail.", "O resumo em português, o documento original e a ponte com o debate de hoje.")}
</main>
"""
    escreve("arquivo", cabeca("Arquivo · Clássicos comentados — Economista Renato Gomes", "Os debates que criaram a economia moderna, lidos no original e explicados em português, com o documento sempre a um clique.", "arquivo/", rel)
            + topo("arquivo/", rel, completo=False) + corpo + rodape(rel))


def pagina_edicao(ed, anterior, proxima):
    rel = "../../"
    pontos = "\n".join(f"      <li><b>{e(t)}.</b> {e(x)}</li>" for t, x in ed["pontos"])
    itens = "\n".join(
        f'        <li><b>{e(t)}</b> ({e(p)}). <a href="https://www.jstor.org/stable/{j}" target="_blank" rel="noopener">JSTOR</a> · '
        f'<a href="https://archive.org/details/jstor-{j}" target="_blank" rel="noopener">Internet Archive (PDF)</a></li>' for t, p, j in ed["itens"])
    nav = []
    if anterior: nav.append(f'<a href="../{anterior["slug"]}/">&larr; Nº {anterior["numero"]} · {e(anterior["titulo"])}</a>')
    if proxima: nav.append(f'<a href="../{proxima["slug"]}/">Nº {proxima["numero"]} · {e(proxima["titulo"])} &rarr;</a>')
    corpo = f"""
<article class="artigo">
  <div class="artigo-topo">
    <span class="chapeu">Arquivo · Nº {ed['numero']} · {e(ed['publicacao'])}, {e(ed['volume'])} ({e(ed['data'])})</span>
    <h1>{e(ed['titulo'])}</h1>
    <p class="olho">{e(ed['chamada'])}</p>
    <div class="barra-autor">
      <div class="mini"><img src="{rel}assets/monograma-branco.png" alt=""></div>
      <div class="quem">
        <b>Comentado por Renato W. Gomes</b>
        <span>Original: “{e(ed['titulo_original'])}” — {e(ed['autores'])}</span>
      </div>
    </div>
  </div>

  <div class="corpo">
    <h2>O que diz o documento</h2>
    <ol>
{pontos}
    </ol>

    <div class="caixa-num">
      <div class="valor">E hoje?</div>
      <div class="exp">{e(ed['hoje'])}</div>
    </div>

    <div class="fontes">
      <h3>Fontes</h3>
      <ol>
{itens}
        <li>Sumário da edição no JSTOR: <a href="https://www.jstor.org/stable/10.2307/{ed['jstor_edicao']}" target="_blank" rel="noopener">{e(ed['publicacao'])}, {e(ed['volume'])}</a>.</li>
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


def pagina_analises():
    rel = "../"
    corpo = f"""
<main class="env">
  <div class="artigo-topo" style="max-width:820px;margin:40px auto 10px">
    <span class="chapeu dado">Análises</span>
    <h1>Contas públicas com fonte</h1>
    <p class="olho">Orçamento, arrecadação, renúncia fiscal, dívida e investimento — lidos no documento oficial (LOA, LDO, Diário Oficial, SICONFI/RREO, IBGE) e explicados em linguagem de gente.</p>
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
      <span class="chapeu">Consultoria · WGSA</span>
      <h3 class="tit tit-g">Planejamento financeiro e tributário</h3>
      <p class="olho">Planejamento contábil, tributário e financeiro para empresas — experiência com mais de 300 clientes. Atendimento pela WGSA Gestão Empresarial.</p>
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
    <p>Sou economista há quinze anos, consultor independente com especialização em Finanças pela Fundação Getúlio Vargas. Já atendi mais de trezentas empresas em planejamento contábil, tributário e financeiro, e trabalhei no mercado financeiro no Rio de Janeiro e em Brasília. Sou sócio-fundador da WGSA Gestão Empresarial e moro em Campo Grande.</p>
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


def sitemap():
    urls = ["", "arquivo/", "analises/", "servicos/", "sobre/"] + [f"arquivo/{ed['slug']}/" for ed in DADOS["edicoes"]]
    hoje = date.today().isoformat()
    x = "\n".join(f"  <url><loc>{DOMINIO}/{u}</loc><lastmod>{hoje}</lastmod></url>" for u in urls)
    open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{x}\n</urlset>\n')
    print("ok site/sitemap.xml")


if __name__ == "__main__":
    pagina_inicio(); pagina_arquivo(); pagina_analises(); pagina_servicos(); pagina_sobre(); pagina_obrigado()
    eds = DADOS["edicoes"]
    for i, ed in enumerate(eds):
        pagina_edicao(ed, eds[i - 1] if i > 0 else None, eds[i + 1] if i + 1 < len(eds) else None)
    sitemap()
