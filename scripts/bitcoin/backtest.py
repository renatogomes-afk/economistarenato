"""Piloto /bitcoin: testa sinais semanais de análise técnica no histórico do bitcoin.

Dados (baixados na hora, fontes públicas):
  - BTC/USD: velas diárias da Coinbase, agrupadas em semanas que fecham no domingo (UTC).
  - Dólar (PTAX venda, série SGS 1) e CDI (taxa diária, série SGS 12): Banco Central do Brasil.
  - Juro do dólar: Fed Funds efetivo (EFFR, Federal Reserve Bank of New York; reserva: série DFF do FRED), o equivalente americano do CDI.
Regras: decisão uma vez por semana; posição inicial = 1 BTC; taxa de 0,25% por compra ou venda; sem alavancagem.
Duas carteiras, cada uma coerente com a sua moeda (ninguém ganha CDI em dólar):
  - Em reais: o bitcoin é cotado em reais (BTC-USD x PTAX do dia, como numa corretora brasileira de BTC/BRL); vender
    o bitcoin dá reais, que rendem CDI (composto dia útil a dia útil); recomprar gasta esses reais na cotação do dia.
  - Em dólares: o bitcoin é cotado em dólares; vender dá dólares, que rendem Fed Funds (composto dia a dia, base 360).
    Não há conversão para reais nem CDI nessa carteira.
Saída: scripts/bitcoin/resultados.json, site/bitcoin/dados.json (lido pela página) e uma tabela no terminal.
"""
import json, math, os, sys, urllib.request, datetime as dt

TAXA = 0.0025
AQUI = os.path.dirname(os.path.abspath(__file__))


def baixa(url, tentativas=5):
    """Baixa JSON; as APIs às vezes devolvem resposta vazia ou erro passageiro, então tenta de novo com espera crescente."""
    import time
    for t in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "research-client"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception:
            if t == tentativas - 1:
                raise
            time.sleep(5 * (t + 1))


def btc_semanal():
    """Velas diárias da Coinbase (BTC-USD) agrupadas em semanas que fecham no domingo (UTC)."""
    dias, ini, hoje = {}, dt.date(2015, 7, 20), dt.date.today()
    while ini <= hoje:
        fim = min(ini + dt.timedelta(days=299), hoje)
        url = (f"https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400"
               f"&start={ini.isoformat()}T00:00:00Z&end={fim.isoformat()}T23:59:59Z")
        for t, lo, hi, op, cl, vol in baixa(url):
            dias[dt.datetime.utcfromtimestamp(int(t)).date()] = (float(hi), float(lo), float(cl))
        ini = fim + dt.timedelta(days=1)
    semanas = {}
    for d in sorted(dias):
        domingo = d + dt.timedelta(days=6 - d.weekday())
        hi, lo, cl = dias[d]
        w = semanas.setdefault(domingo, {"data": domingo, "alta": hi, "baixa": lo, "fech": cl, "ult": d})
        w["alta"], w["baixa"], w["fech"], w["ult"] = max(w["alta"], hi), min(w["baixa"], lo), cl, d
    out = [w for k, w in sorted(semanas.items()) if w["ult"] == k]  # só semanas que já fecharam no domingo
    return out, dias


def sgs(serie, ini):
    # O SGS limita consultas a 10 anos: baixa em blocos.
    out, a = {}, ini
    hoje = dt.date.today()
    while a <= hoje:
        b = min(dt.date(a.year + 9, 12, 31), hoje)
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{serie}/dados?formato=json&dataInicial={a:%d/%m/%Y}&dataFinal={b:%d/%m/%Y}"
        for x in baixa(url):
            d, m, y = x["data"].split("/")
            out[dt.date(int(y), int(m), int(d))] = float(x["valor"])
        a = b + dt.timedelta(days=1)
    return out


def fred(serie, ini, tentativas=3):
    """Série diária do FRED (CSV público, sem chave). Devolve {data: valor}; dias sem dado ("." no CSV) ficam de fora."""
    import time
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={serie}&cosd={ini.isoformat()}"
    for t in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                linhas = r.read().decode().splitlines()
            break
        except Exception:
            if t == tentativas - 1:
                raise
            time.sleep(5 * (t + 1))
    out = {}
    for linha in linhas[1:]:
        partes = linha.split(",")
        try:
            out[dt.date.fromisoformat(partes[0])] = float(partes[1])
        except (ValueError, IndexError):
            pass
    if not out:
        raise ValueError(f"FRED {serie}: resposta sem dados")
    return out


def effr_nyfed(ini):
    """Fed Funds efetivo (EFFR) direto do Federal Reserve Bank of New York, que publica a taxa (dias úteis).
    Baixa ano a ano. Devolve {data: % ao ano}."""
    out, a, hoje = {}, ini, dt.date.today()
    while a <= hoje:
        b = min(dt.date(a.year, 12, 31), hoje)
        url = f"https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json?startDate={a.isoformat()}&endDate={b.isoformat()}"
        for x in baixa(url).get("refRates", []):
            out[dt.date.fromisoformat(x["effectiveDate"])] = float(x["percentRate"])
        a = b + dt.timedelta(days=1)
    if not out:
        raise ValueError("NY Fed: resposta sem dados")
    return out


def fatores_cdi(datas, cdi_d):
    """Quanto R$ 1 no CDI cresce de um domingo ao seguinte: produto das taxas diárias dos dias úteis da semana
    (a SGS 12 só tem dias úteis; a taxa de sexta remunera até segunda). fator[0] = 1."""
    out = [1.0]
    for a, b in zip(datas, datas[1:]):
        f, d = 1.0, a + dt.timedelta(days=1)
        while d <= b:
            f *= 1 + cdi_d.get(d, 0.0) / 100
            d += dt.timedelta(days=1)
        out.append(f)
    return out


def fatores_fed(datas, fed_d):
    """Quanto US$ 1 no Fed Funds cresce de um domingo ao seguinte: taxa/360 por dia corrido, composta dia a dia
    (fim de semana e feriado repetem a taxa do último dia útil, como no mercado americano). fator[0] = 1."""
    out = [1.0]
    for a, b in zip(datas, datas[1:]):
        f, d = 1.0, a
        while d < b:
            f *= 1 + (ultimo_ate(fed_d, d) or 0.0) / 36000
            d += dt.timedelta(days=1)
        out.append(f)
    return out


def ultimo_ate(serie, dia):
    for k in range(10):
        v = serie.get(dia - dt.timedelta(days=k))
        if v is not None:
            return v
    return None


def sma(xs, n, i):
    return sum(xs[i - n + 1:i + 1]) / n if i >= n - 1 else None


def ema_lista(xs, n):
    k, out, e = 2 / (n + 1), [], None
    for x in xs:
        e = x if e is None else x * k + e * (1 - k)
        out.append(e)
    return out


def rsi_lista(xs, n=14):
    out, ganho, perda = [None] * len(xs), 0.0, 0.0
    for i in range(1, len(xs)):
        d = xs[i] - xs[i - 1]
        g, p = max(d, 0), max(-d, 0)
        if i <= n:
            ganho += g / n; perda += p / n
            if i == n:
                out[i] = 100 - 100 / (1 + ganho / perda) if perda else 100
        else:
            ganho = (ganho * (n - 1) + g) / n; perda = (perda * (n - 1) + p) / n
            out[i] = 100 - 100 / (1 + ganho / perda) if perda else 100
    return out


def sinais_fechamento(px):
    """Todos os sinais lidos só no fechamento semanal (versão antiga; serve de comparação em execucao.py)."""
    c = [p["fech"] for p in px]
    n = len(c)
    s = {}
    s["Comprar e segurar"] = [True] * n
    s["Média de 40 semanas"] = [sma(c, 40, i) is not None and c[i] > sma(c, 40, i) for i in range(n)]
    s["Cruzamento 10 x 40 semanas"] = [sma(c, 40, i) is not None and sma(c, 10, i) > sma(c, 40, i) for i in range(n)]
    r = rsi_lista(c)
    est, out = False, []
    for i in range(n):
        if r[i] is not None and i > 0 and r[i - 1] is not None:
            if not est and r[i - 1] < 30 <= r[i]: est = True
            elif est and r[i - 1] > 70 >= r[i]: est = False
        out.append(est)
    s["IFR semanal (30/70)"] = out
    est, out = False, []
    for i in range(n):
        if i >= 20:
            if not est and c[i] > max(c[i - 20:i]): est = True
            elif est and c[i] < min(c[i - 10:i]): est = False
        out.append(est)
    s["Rompimento 20 semanas"] = out
    m = [a - b for a, b in zip(ema_lista(c, 12), ema_lista(c, 26))]
    sig = ema_lista(m, 9)
    s["MACD semanal"] = [i >= 35 and m[i] > sig[i] for i in range(n)]
    # Dow: topo/fundo de oscilação = pivô com 2 semanas de cada lado (confirmado 2 semanas depois)
    est, out, topo, fundo = False, [], None, None
    for i in range(n):
        j = i - 2
        if j >= 2:
            if c[j] == max(c[j - 2:j + 3]): topo = c[j]
            if c[j] == min(c[j - 2:j + 3]): fundo = c[j]
        if topo is not None and not est and c[i] > topo: est = True
        elif fundo is not None and est and c[i] < fundo: est = False
        out.append(est)
    s["Topos e fundos (Dow)"] = out
    est, out, pct_ant = False, [], None
    for i in range(n):
        pct = None
        if i >= 52:
            janela = c[i - 52:i]
            pct = 100 * sum(1 for x in janela if x < c[i]) / 52
            if pct_ant is not None:
                if not est and pct_ant < 20 <= pct: est = True
                elif est and pct_ant > 80 >= pct: est = False
        pct_ant = pct
        out.append(est)
    s["Faixas de percentis 52 semanas"] = out
    return s


# ---------- ordens no book ----------
# Regra de execução (decisão do Renato, 24/11/2026): se a regra define um nível de preço conhecido antes da semana,
# deixa-se uma ordem stop no book nesse nível, executada no meio da semana quando a máxima ou a mínima toca o nível
# (no preço do nível, ou na abertura se a semana já abrir além dele). Se a regra depende do fechamento, executa-se
# no próprio fechamento em que o sinal aparece. Cada função devolve (posição ao fim de cada semana, preço da execução
# em US$ em cada semana, nível da ordem para a semana seguinte).
def book_media(px, n=40):
    c = [p["fech"] for p in px]
    est, alvo, preco = False, [], []
    for i, p in enumerate(px):
        pr = p["fech"]
        if i > n:
            nivel, ab = sum(c[i - n:i]) / n, c[i - 1]  # média até a semana anterior, conhecida no domingo
            if not est and p["alta"] > nivel: est, pr = True, max(nivel, ab)
            elif est and p["baixa"] < nivel: est, pr = False, min(nivel, ab)
        alvo.append(est); preco.append(pr)
    return alvo, preco, ("venda" if est else "compra", sum(c[-n:]) / n)


def book_romp(px, e=20, x=10):
    c = [p["fech"] for p in px]
    est, alvo, preco = False, [], []
    for i, p in enumerate(px):
        pr = p["fech"]
        if i >= e:
            ab = c[i - 1]
            if not est:
                nivel = max(c[i - e:i])
                if p["alta"] > nivel: est, pr = True, max(nivel, ab)
            else:
                nivel = min(c[i - x:i])
                if p["baixa"] < nivel: est, pr = False, min(nivel, ab)
        alvo.append(est); preco.append(pr)
    return alvo, preco, ("venda", min(c[-x:])) if est else ("compra", max(c[-e:]))


def book_dow(px, w=2):
    c = [p["fech"] for p in px]
    est, alvo, preco, topo, fundo = False, [], [], None, None

    def pivos(i, topo, fundo):
        j = i - 1 - w  # pivôs confirmados até a semana anterior
        if j >= w:
            jan = c[j - w:j + w + 1]
            if c[j] == max(jan): topo = c[j]
            if c[j] == min(jan): fundo = c[j]
        return topo, fundo
    for i, p in enumerate(px):
        pr = p["fech"]
        topo, fundo = pivos(i, topo, fundo)
        if i > 0:
            ab = c[i - 1]
            if topo is not None and not est and p["alta"] > topo: est, pr = True, max(topo, ab)
            elif fundo is not None and est and p["baixa"] < fundo: est, pr = False, min(fundo, ab)
        alvo.append(est); preco.append(pr)
    topo, fundo = pivos(len(px), topo, fundo)
    return alvo, preco, ("venda", fundo) if est else ("compra", topo)


def niveis_pct(c, i, n, lo, hi):
    jan = sorted(c[i - n:i])
    return jan[int(len(jan) * lo / 100)], jan[min(len(jan) - 1, int(len(jan) * hi / 100))]


def book_pct(px, n=52, lo=20, hi=80):
    """Faixas de percentis: compra quando o preço sobe de volta acima do nível do percentil 20 (estando abaixo dele no
    domingo); vende quando cai de volta abaixo do nível do percentil 80 (estando acima dele no domingo)."""
    c = [p["fech"] for p in px]
    est, alvo, preco = False, [], []
    for i, p in enumerate(px):
        pr = p["fech"]
        if i > n:
            n_lo, n_hi = niveis_pct(c, i, n, lo, hi)
            ab = c[i - 1]
            if not est and ab < n_lo and p["alta"] > n_lo: est, pr = True, max(n_lo, ab)
            elif est and ab > n_hi and p["baixa"] < n_hi: est, pr = False, min(n_hi, ab)
        alvo.append(est); preco.append(pr)
    n_lo, n_hi = niveis_pct(c, len(c), n, lo, hi)
    ordem = ("venda", n_hi) if est and c[-1] > n_hi else ("compra", n_lo) if not est and c[-1] < n_lo else None
    return alvo, preco, ordem


BOOK = {"Média de 40 semanas": book_media, "Rompimento 20 semanas": book_romp,
        "Topos e fundos (Dow)": book_dow, "Faixas de percentis 52 semanas": book_pct}


def sinais(px):
    """Sinais usados no site: as quatro regras com nível de preço viram ordens no book; as demais, fechamento."""
    s = sinais_fechamento(px)
    for nome, f in BOOK.items():
        s[nome] = f(px)[0]
    return s


VOTANTES = ["Média de 40 semanas", "Cruzamento 10 x 40 semanas", "IFR semanal (30/70)", "Rompimento 20 semanas",
            "MACD semanal", "Topos e fundos (Dow)", "Faixas de percentis 52 semanas"]
CONSENSOS = [7, 6, 5, 4]  # placares mínimos: 7 x 0 (unanimidade), 6 x 1, 5 x 2, 4 x 3 (maioria simples)


def nome_consenso(k):
    return f"Consenso {k} x {len(VOTANTES) - k}"


def consenso(s, k):
    """Entra quando pelo menos k dos 7 sinais estão comprados; sai quando pelo menos k estão fora; senão, mantém."""
    n, est, out = len(s[VOTANTES[0]]), True, []
    for i in range(n):
        votos = sum(s[v][i] for v in VOTANTES)
        if votos >= k: est = True
        elif len(VOTANTES) - votos >= k: est = False
        out.append(est)
    return out


def simula(px, dentro, conv, juros, ini, preco=None):
    """Carteira numa moeda só. conv[i]: unidades da moeda por US$ na semana i (PTAX para reais; 1 para dólares);
    juros[i]: quanto o caixa nessa moeda cresce da semana i-1 à i (CDI para reais; Fed Funds para dólares).
    dentro[i]: posição ao fim da semana i. Sem preco, a troca sai no fechamento da semana i (regra de fechamento).
    Com preco (US$), a troca sai no meio da semana i, nesse preço (ordem no book), com metade da semana no caixa."""
    datas = [p["data"] for p in px]
    c = [p["fech"] * conv[k] for k, p in enumerate(px)]  # preço do bitcoin na moeda da carteira
    btc, caixa, trocas, semanas_dentro = 1.0, 0.0, 0, 0
    pos = True  # começa com 1 BTC
    if not dentro[ini]:
        caixa, btc, pos, trocas = c[ini] * (1 - TAXA), 0.0, False, 1
    valores, desde = [], datas[ini]
    for i in range(ini, len(px)):
        if i > ini:
            fator = juros[i]
            if dentro[i] != pos:
                if preco is None:
                    if dentro[i]: btc, caixa = caixa * fator / c[i] * (1 - TAXA), 0.0
                    else: caixa, btc = btc * c[i] * (1 - TAXA), 0.0
                else:
                    pr = preco[i] * conv[i]
                    if dentro[i]: btc, caixa = caixa * fator ** 0.5 / pr * (1 - TAXA), 0.0
                    else: caixa, btc = btc * pr * (1 - TAXA) * fator ** 0.5, 0.0
                pos, trocas = dentro[i], trocas + 1
            elif not pos:
                caixa *= fator
        semanas_dentro += pos
        if i > ini and dentro[i] != dentro[i - 1]:
            desde = datas[i]
        valores.append(btc * c[i] + caixa)
    anos = (datas[-1] - datas[ini]).days / 365.25
    rets = [valores[k] / valores[k - 1] - 1 for k in range(1, len(valores))]
    media = sum(rets) / len(rets)
    vol = math.sqrt(sum((x - media) ** 2 for x in rets) / (len(rets) - 1)) * math.sqrt(52)
    pico, pior = valores[0], 0.0
    for v in valores:
        pico = max(pico, v); pior = min(pior, v / pico - 1)
    return {"btc_final": valores[-1] / c[-1], "retorno_anual": (valores[-1] / valores[0]) ** (1 / anos) - 1,
            "volatilidade_anual": vol, "pior_queda": pior, "operacoes": trocas,
            "tempo_comprado": semanas_dentro / len(valores),
            "_valores": valores, "_estado": {"comprado": pos, "btc": btc, "caixa_brl": caixa, "desde": desde.isoformat()}}


INI_SIM = 52  # semanas de folga antes do início do teste
INICIO_ACOMP = dt.date(2026, 11, 22)  # fechamento de domingo antes do lançamento do piloto


def retornos_anuais(datas, valores, caixa="Só CDI"):
    """Retorno de cada ano civil (na moeda dos valores recebidos; a página usa dólares) (valor no último domingo do ano sobre o do ano anterior) e dos últimos 5 anos."""
    fim_ano = {}
    for k, d in enumerate(datas):
        fim_ano[d.year] = k
    anos = sorted(fim_ano)[1:]
    ult = len(datas) - 1
    k5 = max(k for k, d in enumerate(datas) if d <= datas[-1].replace(year=datas[-1].year - 5))
    anos_5 = (datas[ult] - datas[k5]).days / 365.25
    return {"anos": anos, "caixa": caixa, "ultimo": datas[ult].isoformat(), "inicio_5a": datas[k5].isoformat(),
            "por_estrategia": {n: [round(v[fim_ano[a]] / v[fim_ano[a - 1]] - 1, 4) for a in anos] for n, v in valores.items()},
            "cinco_anos_aa": {n: round((v[ult] / v[k5]) ** (1 / anos_5) - 1, 4) for n, v in valores.items()},
            "inicio_total": datas[0].isoformat(),
            "total_acum": {n: round(v[ult] / v[0] - 1, 4) for n, v in valores.items()},
            "total_aa": {n: round((v[ult] / v[0]) ** (365.25 / (datas[ult] - datas[0]).days) - 1, 4) for n, v in valores.items()}}


GRAF_SEMANAS = 78  # um ano e meio de velas semanais no gráfico da página


def grafico_semanal(px, sin):
    """Velas semanais (USD) e o sinal de cada estratégia, semana a semana, para o gráfico com marcadores."""
    n = min(GRAF_SEMANAS, len(px) - 1)
    k0 = len(px) - n
    return {"datas": [p["data"].isoformat() for p in px[k0:]],
            "abre": [round(px[k - 1]["fech"], 2) for k in range(k0, len(px))],
            "alta": [round(p["alta"], 2) for p in px[k0:]],
            "baixa": [round(p["baixa"], 2) for p in px[k0:]],
            "fech": [round(p["fech"], 2) for p in px[k0:]],
            "sinal_anterior": {nome: int(d[k0 - 1]) for nome, d in sin.items() if nome != "Comprar e segurar"},
            "sinais": {nome: [int(x) for x in d[k0:]] for nome, d in sin.items() if nome != "Comprar e segurar"},
            # histórico completo de fechamentos: a página recalcula os sinais ao vivo com a semana em curso
            "hist_fech": [round(p["fech"], 2) for p in px],
            "hist_alta": [round(p["alta"], 2) for p in px], "hist_baixa": [round(p["baixa"], 2) for p in px],
            "consenso_limites": CONSENSOS, "votantes": VOTANTES}


BOLETINS = os.path.join(AQUI, "boletins")


def grava_boletim(px, brl, sin, book, datas, valores, valores_usd, votos, k0):
    """Boletim semanal: registro do que cada estratégia fez na semana que fechou no domingo. É gravado uma vez por
    semana e nunca reescrito, para o arquivo ficar como foi publicado (mesmo que regras ou dados mudem depois)."""
    if k0 is None:
        return
    os.makedirs(BOLETINS, exist_ok=True)
    data = datas[-1].isoformat()
    arq = os.path.join(BOLETINS, f"{data}.json")
    if os.path.exists(arq):
        return
    n = len(px) - 1
    k = len(datas) - 1
    est = []
    for nome, v in valores.items():
        vu = valores_usd[CAIXA_USD if nome == "Só CDI" else nome]
        s = sin.get(nome)
        antes, agora = (bool(s[n - 1]), bool(s[n])) if s else (False, False)
        operou = antes != agora
        preco = None
        if operou:
            preco = round(book[nome][1][n], 2) if nome in book else round(px[n]["fech"], 2)
        ordem = book[nome][2] if nome in book else None
        est.append({"nome": nome, "antes": antes, "agora": agora, "operou": operou, "preco_usd": preco,
                    "ordem_book": {"tipo": ordem[0], "nivel_usd": round(ordem[1], 2)} if ordem and ordem[1] is not None else None,
                    "semana_brl": round(v[k] / v[k - 1] - 1, 5), "semana_usd": round(vu[k] / vu[k - 1] - 1, 5),
                    "desde_lancamento_brl": round(v[k] / v[k0] - 1, 5) if k0 <= k else None,
                    "btc": round(v[k] / (px[n]["fech"] * brl[n]), 5)})
    json.dump({"data": data, "gerado_em": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
               "inicio_acompanhamento": datas[k0].isoformat(),
               "btc_usd": {"fech": px[n]["fech"], "anterior": px[n - 1]["fech"], "alta": px[n]["alta"], "baixa": px[n]["baixa"]},
               "ptax": brl[n], "votos": votos[n], "votos_antes": votos[n - 1],
               "votos_por_sinal": {v: bool(sin[v][n]) for v in VOTANTES},
               "votos_por_sinal_antes": {v: bool(sin[v][n - 1]) for v in VOTANTES},
               "estrategias": est}, open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


CAIXA_USD = "Só Fed Funds"  # benchmark de caixa da carteira em dólares (o "Só CDI" da carteira em reais)


def juro_usd(datas):
    """Fatores semanais do Fed Funds: NY Fed (fonte oficial da EFFR); se falhar, FRED (série DFF); se os dois
    falharem, reaproveita os fatores já gravados e repete o último nas semanas novas (avisa no terminal), para o robô
    semanal não parar por causa de uma fonte."""
    ini = datas[0] - dt.timedelta(days=15)
    erros = []
    for nome, f in (("NY Fed", effr_nyfed), ("FRED", lambda d: fred("DFF", d))):
        try:
            fed_d = f(ini)
            return fatores_fed(datas, fed_d), [ultimo_ate(fed_d, d) or 0.0 for d in datas]
        except Exception as erro:
            erros.append(f"{nome}: {erro}")
    print(f"AVISO: juro do dólar indisponível ({'; '.join(erros)}); usando os fatores do Fed Funds já gravados.")
    P = json.load(open(os.path.join(AQUI, "precos_semanais.json"), encoding="utf-8"))
    if not P.get("fator_fed"):
        raise RuntimeError("sem juro do dólar: " + "; ".join(erros))
    velho, taxa = dict(zip(P["datas"], P["fator_fed"])), dict(zip(P["datas"], P["fed"]))
    f, t, ult_f, ult_t = [], [], 1.0, 0.0
    for k, d in enumerate(datas):
        ult_f, ult_t = velho.get(d.isoformat(), ult_f), taxa.get(d.isoformat(), ult_t)
        f.append(1.0 if k == 0 else ult_f); t.append(ult_t)
    return f, t


def main():
    px, dias = btc_semanal()
    ini_data = px[0]["data"]
    ptax = sgs(1, ini_data - dt.timedelta(days=15))
    cdi_d = sgs(12, ini_data - dt.timedelta(days=15))
    datas_px = [p["data"] for p in px]
    brl = [ultimo_ate(ptax, d) for d in datas_px]
    cdi = [ultimo_ate(cdi_d, d) or 0.0 for d in datas_px]
    f_cdi = fatores_cdi(datas_px, cdi_d)
    f_fed, fed = juro_usd(datas_px)
    # Cópia dos dados semanais usados (preço, dólar, CDI e Fed Funds), para a otimização rodar sem baixar de novo.
    json.dump({"datas": [d.isoformat() for d in datas_px], "fech": [p["fech"] for p in px], "alta": [p["alta"] for p in px],
               "baixa": [p["baixa"] for p in px], "ptax": brl, "cdi": cdi, "fator_cdi": f_cdi, "fed": fed, "fator_fed": f_fed},
              open(os.path.join(AQUI, "precos_semanais.json"), "w", encoding="utf-8"), separators=(",", ":"))
    ini = INI_SIM  # um ano de histórico para todos os indicadores terem dados
    sin = sinais(px)
    votos = [sum(sin[v][i] for v in VOTANTES) for i in range(len(px))]
    for k in CONSENSOS:
        sin[nome_consenso(k)] = consenso(sin, k)
    # Regras de nível: ordem no book durante a semana. Regras de fechamento: executa no próprio fechamento do sinal.
    book = {nome: f(px) for nome, f in BOOK.items()}
    res = {nome: simula(px, d, brl, f_cdi, ini, book[nome][1] if nome in book else None) for nome, d in sin.items()}
    so_cdi = simula(px, [False] * len(px), brl, f_cdi, ini)
    so_cdi["operacoes"] = 1
    res["Só CDI"] = so_cdi
    # Mesmas regras, carteira em dólares: BTC em US$ e caixa no Fed Funds, sem passar pelo real nem pelo CDI.
    usd1 = [1.0] * len(px)
    res_usd = {nome: simula(px, d, usd1, f_fed, ini, book[nome][1] if nome in book else None) for nome, d in sin.items()}
    res_usd[CAIXA_USD] = simula(px, [False] * len(px), usd1, f_fed, ini)
    valores_usd = {nome: [round(x, 2) for x in r.pop("_valores")] for nome, r in res_usd.items()}
    datas = [p["data"] for p in px][ini:]
    c_brl = [px[k]["fech"] * brl[k] for k in range(ini, len(px))]
    k0 = next((k for k, d in enumerate(datas) if d >= INICIO_ACOMP), None)
    curvas, tabela, valores = {}, [], {}
    for nome, r in res.items():
        v = r.pop("_valores"); est = r.pop("_estado")
        valores[nome] = [round(x, 2) for x in v]
        curvas[nome] = [round(x / cc, 4) for x, cc in zip(v, c_brl)]
        # sinal da última semana fechada: é o que vale para a semana em curso
        proximo = sin[nome][-1] if nome in sin else False
        ordem = book[nome][2] if nome in book else None
        ru = res_usd[CAIXA_USD if nome == "Só CDI" else nome]
        r["retorno_anual_brl"] = r.pop("retorno_anual")
        tabela.append({"nome": nome, **r, **est, "btc_final_usd": ru["btc_final"], "retorno_anual_usd": ru["retorno_anual"],
                       "pior_queda_usd": ru["pior_queda"], "sinal_para_esta_semana": proximo,
                       "comprado_antes": bool(sin[nome][-2]) if nome in sin else False,
                       "ordem_book": {"tipo": ordem[0], "nivel_usd": round(ordem[1], 2)} if ordem and ordem[1] is not None else None,
                       "valor_inicio_acomp_brl": v[k0] if k0 is not None else None})
    ult = px[-1]
    saida = {"gerado_em": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "inicio": datas[0].isoformat(), "fim": datas[-1].isoformat(),
             "semanas": len(datas), "taxa_por_operacao": TAXA, "regras_book": list(BOOK), "inicio_acompanhamento": INICIO_ACOMP.isoformat(),
             "ultimo_fech_usd": ult["fech"], "ultimo_fech_brl": ult["fech"] * brl[-1], "ptax": brl[-1],
             "fontes": {"btc": "Coinbase, velas diárias BTC-USD, semana fechando no domingo (UTC)", "dolar": "BCB/SGS 1 (PTAX venda)", "cdi": "BCB/SGS 12",
                        "juro_usd": "Federal Reserve Bank of New York (EFFR, Fed Funds efetivo)"},
             "caixa": {"brl": "Só CDI", "usd": CAIXA_USD},
             "consenso": {"limites": CONSENSOS, "votantes": VOTANTES, "votos_agora": votos[-1],
                          "votos_por_sinal": {v: bool(sin[v][-1]) for v in VOTANTES}},
             "grafico": grafico_semanal(px, sin),
             "anuais": retornos_anuais(datas, valores),
             "anuais_usd": retornos_anuais(datas, valores_usd, CAIXA_USD),
             "estrategias": tabela, "curvas": {"datas": [d.isoformat() for d in datas], **curvas}}
    for destino in (os.path.join(AQUI, "resultados.json"), os.path.join(AQUI, "..", "..", "site", "bitcoin", "dados.json")):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        json.dump(saida, open(destino, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    # Valor semanal em reais de cada estratégia (base dos retornos semanais, mensais e anuais); não vai para o site.
    semanal = {"datas": [d.isoformat() for d in datas], "btc_brl": [round(x, 2) for x in c_brl], "ptax": [round(x, 4) for x in brl[INI_SIM:]],
               "valores_brl": valores, "valores_usd": valores_usd}
    # Vai também para o site: a página recalcula os retornos na janela que o leitor escolher.
    for destino in (os.path.join(AQUI, "valores_semanais.json"), os.path.join(AQUI, "..", "..", "site", "bitcoin", "valores.json")):
        json.dump(semanal, open(destino, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    grava_boletim(px, brl, sin, book, datas, valores, valores_usd, votos, k0)
    print(f"Período: {saida['inicio']} a {saida['fim']} ({saida['semanas']} semanas). Taxa {TAXA:.2%} por operação.")
    print(f"{'Sinal':34} {'BTC final':>9} {'a.a. R$':>8} {'Vol':>6} {'Pior queda':>10} {'Oper.':>5} {'Comprado':>8} {'Agora':>6}")
    print(f"Placar desta semana: {votos[-1]} de 7 sinais comprados.")
    for r in sorted(tabela, key=lambda x: -x["btc_final"]):
        print(f"{r['nome']:34} {r['btc_final']:9.3f} {r['retorno_anual_brl']:8.1%} {r['volatilidade_anual']:6.0%} {r['pior_queda']:10.1%} {r['operacoes']:5d} {r['tempo_comprado']:8.0%} {'dentro' if r['sinal_para_esta_semana'] else 'fora':>6}")
    A, B = saida["anuais_usd"], saida["anuais"]
    print(f"\nCarteira em dólares (caixa no Fed Funds) x em reais (caixa no CDI). 5 anos ao ano desde {A['inicio_5a']}.")
    print(f"{'Sinal':34} {'BTC US$':>8} {'a.a. US$':>8} {'5a US$':>7} {'BTC R$':>7} {'a.a. R$':>8} {'5a R$':>7}")
    for r in sorted(tabela, key=lambda x: -x["btc_final_usd"]):
        n, nu = r["nome"], (CAIXA_USD if r["nome"] == "Só CDI" else r["nome"])
        print(f"{nu:34} {r['btc_final_usd']:8.3f} {r['retorno_anual_usd']:8.1%} {A['cinco_anos_aa'][nu]:7.1%} {r['btc_final']:7.3f} {r['retorno_anual_brl']:8.1%} {B['cinco_anos_aa'][n]:7.1%}")


if __name__ == "__main__":
    main()
