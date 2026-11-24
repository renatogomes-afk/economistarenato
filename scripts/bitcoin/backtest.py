"""Piloto /bitcoin: testa sinais semanais de análise técnica no histórico do bitcoin.

Dados (baixados na hora, fontes públicas):
  - BTC/USD semanal: Kraken, OHLC público (XBTUSD, intervalo de 1 semana).
  - Dólar (PTAX venda, série SGS 1) e CDI (taxa diária, série SGS 12): Banco Central do Brasil.
Regras: decisão uma vez por semana, no fechamento semanal; posição inicial = 1 BTC;
fora do mercado o dinheiro rende CDI; taxa de 0,25% por compra ou venda; sem alavancagem.
Saída: scripts/bitcoin/resultados.json e uma tabela no terminal.
"""
import json, math, os, sys, urllib.request, datetime as dt

TAXA = 0.0025
AQUI = os.path.dirname(os.path.abspath(__file__))


def baixa(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-client"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def btc_semanal():
    d = baixa("https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=10080")
    if d.get("error"):
        raise RuntimeError(d["error"])
    linhas = next(v for k, v in d["result"].items() if k != "last")
    out = []
    for t, o, h, l, c, *_ in linhas:
        out.append({"data": dt.datetime.utcfromtimestamp(int(t)).date(), "alta": float(h), "baixa": float(l), "fech": float(c)})
    return out[:-1]  # a última semana ainda não fechou


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


def simula(px, dentro, brl, cdi, ini):
    datas = [p["data"] for p in px]
    c = [p["fech"] * brl[k] for k, p in enumerate(px)]  # preço em reais
    btc, caixa, trocas, semanas_dentro = 1.0, 0.0, 0, 0
    pos = True  # começa com 1 BTC
    if not dentro[ini]:
        caixa, btc, pos, trocas = c[ini] * (1 - TAXA), 0.0, False, 1
    valores = []
    for i in range(ini, len(px)):
        if i > ini and not pos:
            dias = (datas[i] - datas[i - 1]).days
            caixa *= (1 + cdi[i - 1] / 100) ** (dias * 5 / 7)  # CDI diário em dias úteis aproximados
        if i > ini and dentro[i] != pos:
            if dentro[i]: btc, caixa = caixa / c[i] * (1 - TAXA), 0.0
            else: caixa, btc = btc * c[i] * (1 - TAXA), 0.0
            pos, trocas = dentro[i], trocas + 1
        semanas_dentro += pos
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
            "tempo_comprado": semanas_dentro / len(valores)}


def main():
    px = btc_semanal()
    ini_data = px[0]["data"]
    ptax = sgs(1, ini_data - dt.timedelta(days=15))
    cdi_d = sgs(12, ini_data - dt.timedelta(days=15))
    brl = [ultimo_ate(ptax, p["data"]) for p in px]
    cdi = [ultimo_ate(cdi_d, p["data"]) or 0.0 for p in px]
    ini = 52  # um ano de histórico para todos os indicadores terem dados
    res = {nome: simula(px, d, brl, cdi, ini) for nome, d in sinais(px).items()}
    # CDI puro: vende 1 BTC no início e deixa no CDI
    so_cdi = simula(px, [False] * len(px), brl, cdi, ini)
    so_cdi["operacoes"] = 1
    res["Só CDI (vende tudo no início)"] = so_cdi
    saida = {"gerado_em": dt.date.today().isoformat(), "inicio": px[ini]["data"].isoformat(), "fim": px[-1]["data"].isoformat(),
             "semanas": len(px) - ini, "taxa_por_operacao": TAXA,
             "fontes": {"btc": "Kraken, OHLC semanal XBTUSD", "dolar": "BCB/SGS 1 (PTAX venda)", "cdi": "BCB/SGS 12"},
             "resultados": res}
    json.dump(saida, open(os.path.join(AQUI, "resultados.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Período: {saida['inicio']} a {saida['fim']} ({saida['semanas']} semanas). Taxa {TAXA:.2%} por operação.")
    print(f"{'Sinal':34} {'BTC final':>9} {'a.a. R$':>8} {'Vol':>6} {'Pior queda':>10} {'Oper.':>5} {'Comprado':>8}")
    for nome, r in sorted(res.items(), key=lambda kv: -kv[1]["btc_final"]):
        print(f"{nome:34} {r['btc_final']:9.3f} {r['retorno_anual_brl']:8.1%} {r['volatilidade_anual']:6.0%} {r['pior_queda']:10.1%} {r['operacoes']:5d} {r['tempo_comprado']:8.0%}")


if __name__ == "__main__":
    main()
