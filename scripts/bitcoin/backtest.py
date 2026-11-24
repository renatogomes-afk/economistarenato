"""Piloto /bitcoin: testa sinais semanais de análise técnica no histórico do bitcoin.

Dados (baixados na hora, fontes públicas):
  - BTC/USD: velas diárias da Coinbase, agrupadas em semanas que fecham no domingo (UTC).
  - Dólar (PTAX venda, série SGS 1) e CDI (taxa diária, série SGS 12): Banco Central do Brasil.
Regras: decisão uma vez por semana; o sinal do fechamento de uma semana é executado no fechamento da seguinte; posição inicial = 1 BTC;
fora do mercado o dinheiro rende CDI; taxa de 0,25% por compra ou venda; sem alavancagem.
Saída: scripts/bitcoin/resultados.json, site/bitcoin/dados.json (lido pela página) e uma tabela no terminal.
"""
import json, math, os, sys, urllib.request, datetime as dt

TAXA = 0.0025
AQUI = os.path.dirname(os.path.abspath(__file__))


def baixa(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-client"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


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


def sinais(px):
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


def simula(px, dentro, brl, cdi, ini):
    datas = [p["data"] for p in px]
    c = [p["fech"] * brl[k] for k, p in enumerate(px)]  # preço em reais
    btc, caixa, trocas, semanas_dentro = 1.0, 0.0, 0, 0
    pos = True  # começa com 1 BTC
    if not dentro[ini]:
        caixa, btc, pos, trocas = c[ini] * (1 - TAXA), 0.0, False, 1
    valores, desde = [], datas[ini]
    for i in range(ini, len(px)):
        if i > ini and not pos:
            dias = (datas[i] - datas[i - 1]).days
            caixa *= (1 + cdi[i - 1] / 100) ** (dias * 5 / 7)  # CDI diário em dias úteis aproximados
        if i > ini and dentro[i] != pos:
            if dentro[i]: btc, caixa = caixa / c[i] * (1 - TAXA), 0.0
            else: caixa, btc = btc * c[i] * (1 - TAXA), 0.0
            pos, trocas = dentro[i], trocas + 1
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
    return {"btc_final": valores[-1] / c[-1], "retorno_anual_brl": (valores[-1] / valores[0]) ** (1 / anos) - 1,
            "volatilidade_anual": vol, "pior_queda": pior, "operacoes": trocas,
            "tempo_comprado": semanas_dentro / len(valores),
            "_valores": valores, "_estado": {"comprado": pos, "btc": btc, "caixa_brl": caixa, "desde": desde.isoformat()}}


INICIO_ACOMP = dt.date(2026, 11, 22)  # fechamento de domingo antes do lançamento do piloto


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
            "consenso_limites": CONSENSOS, "votantes": VOTANTES}


def main():
    px, dias = btc_semanal()
    ini_data = px[0]["data"]
    ptax = sgs(1, ini_data - dt.timedelta(days=15))
    cdi_d = sgs(12, ini_data - dt.timedelta(days=15))
    brl = [ultimo_ate(ptax, p["data"]) for p in px]
    cdi = [ultimo_ate(cdi_d, p["data"]) or 0.0 for p in px]
    ini = 52  # um ano de histórico para todos os indicadores terem dados
    sin = sinais(px)
    votos = [sum(sin[v][i] for v in VOTANTES) for i in range(len(px))]
    for k in CONSENSOS:
        sin[nome_consenso(k)] = consenso(sin, k)
    # Sinal visto no fechamento da semana t é executado no fechamento da semana t+1 (sem olhar o futuro).
    res = {nome: simula(px, [d[0]] + d[:-1], brl, cdi, ini) for nome, d in sin.items()}
    so_cdi = simula(px, [False] * len(px), brl, cdi, ini)
    so_cdi["operacoes"] = 1
    res["Só CDI"] = so_cdi
    datas = [p["data"] for p in px][ini:]
    c_brl = [px[k]["fech"] * brl[k] for k in range(ini, len(px))]
    k0 = next((k for k, d in enumerate(datas) if d >= INICIO_ACOMP), None)
    curvas, tabela = {}, []
    for nome, r in res.items():
        v = r.pop("_valores"); est = r.pop("_estado")
        curvas[nome] = [round(x / cc, 4) for x, cc in zip(v, c_brl)]
        # sinal da última semana fechada: é o que vale para a semana em curso
        proximo = sin[nome][-1] if nome in sin else False
        tabela.append({"nome": nome, **r, **est, "sinal_para_esta_semana": proximo,
                       "valor_inicio_acomp_brl": v[k0] if k0 is not None else None})
    ult = px[-1]
    saida = {"gerado_em": dt.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), "inicio": datas[0].isoformat(), "fim": datas[-1].isoformat(),
             "semanas": len(datas), "taxa_por_operacao": TAXA, "inicio_acompanhamento": INICIO_ACOMP.isoformat(),
             "ultimo_fech_usd": ult["fech"], "ultimo_fech_brl": ult["fech"] * brl[-1], "ptax": brl[-1],
             "fontes": {"btc": "Coinbase, velas diárias BTC-USD, semana fechando no domingo (UTC)", "dolar": "BCB/SGS 1 (PTAX venda)", "cdi": "BCB/SGS 12"},
             "consenso": {"limites": CONSENSOS, "votantes": VOTANTES, "votos_agora": votos[-1],
                          "votos_por_sinal": {v: bool(sin[v][-1]) for v in VOTANTES}},
             "grafico": grafico_semanal(px, sin),
             "estrategias": tabela, "curvas": {"datas": [d.isoformat() for d in datas], **curvas}}
    for destino in (os.path.join(AQUI, "resultados.json"), os.path.join(AQUI, "..", "..", "site", "bitcoin", "dados.json")):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        json.dump(saida, open(destino, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"Período: {saida['inicio']} a {saida['fim']} ({saida['semanas']} semanas). Taxa {TAXA:.2%} por operação.")
    print(f"{'Sinal':34} {'BTC final':>9} {'a.a. R$':>8} {'Vol':>6} {'Pior queda':>10} {'Oper.':>5} {'Comprado':>8} {'Agora':>6}")
    print(f"Placar desta semana: {votos[-1]} de 7 sinais comprados.")
    for r in sorted(tabela, key=lambda x: -x["btc_final"]):
        print(f"{r['nome']:34} {r['btc_final']:9.3f} {r['retorno_anual_brl']:8.1%} {r['volatilidade_anual']:6.0%} {r['pior_queda']:10.1%} {r['operacoes']:5d} {r['tempo_comprado']:8.0%} {'dentro' if r['sinal_para_esta_semana'] else 'fora':>6}")


if __name__ == "__main__":
    main()
