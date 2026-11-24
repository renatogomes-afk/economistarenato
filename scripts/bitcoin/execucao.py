"""Quanto a forma de execução muda os resultados do piloto /bitcoin.

Três premissas, com os mesmos sinais, 0,25% por operação e CDI quando fora:
  1. Fechamento seguinte (premissa atual, conservadora): o sinal do fechamento de domingo é executado no fechamento do
     domingo seguinte. Equivale a decidir com calma e operar uma semana depois.
  2. Ordem no fechamento: a regra é conferida minutos antes do fechamento de domingo e a ordem sai no mesmo fechamento
     (o bitcoin negocia 24 horas, então dá para operar no fechamento semanal). Os sinais são os mesmos; só some a semana de atraso.
  3. Ordens no book: para as regras que definem um nível de preço conhecido antes da semana (rompimento, topos e fundos,
     média de 40 semanas, faixas de percentis), deixa-se uma ordem stop no nível. Ela executa no meio da semana, quando
     a máxima ou a mínima da semana toca o nível, no preço do nível (ou na abertura, se a semana já abrir além dele).
     As regras que dependem do fechamento (cruzamento de médias, IFR, MACD) ficam como na premissa 2.
Saída: scripts/bitcoin/execucao.json e uma tabela no terminal.
"""
import json, math, os, sys, datetime as dt, statistics as st

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backtest as bt  # noqa: E402
import otimiza as ot  # noqa: E402

INI = 52
TAXA = bt.TAXA


def simula_exec(px, brl, cdi, alvo, preco, ini=INI):
    """alvo[i]: posição ao fim da semana i; preco[i]: preço em US$ da execução na semana i, se a posição mudar."""
    datas = [p["data"] for p in px]
    btc, caixa, pos, trocas, valores = 1.0, 0.0, True, 0, []
    if not alvo[ini]:
        caixa, btc, pos, trocas = px[ini]["fech"] * brl[ini] * (1 - TAXA), 0.0, False, 1
    valores.append(btc * px[ini]["fech"] * brl[ini] + caixa)
    for i in range(ini + 1, len(px)):
        dias = (datas[i] - datas[i - 1]).days
        if alvo[i] != pos:
            pr = preco[i] * brl[i]
            if not pos:
                caixa *= (1 + cdi[i - 1] / 100) ** (dias * 5 / 7 / 2)  # metade da semana no CDI, em média
                btc, caixa = caixa / pr * (1 - TAXA), 0.0
            else:
                caixa, btc = btc * pr * (1 - TAXA), 0.0
                caixa *= (1 + cdi[i - 1] / 100) ** (dias * 5 / 7 / 2)
            pos, trocas = alvo[i], trocas + 1
        elif not pos:
            caixa *= (1 + cdi[i - 1] / 100) ** (dias * 5 / 7)
        valores.append(btc * px[i]["fech"] * brl[i] + caixa)
    return valores, trocas


# ---------- premissa 3: ordens stop em níveis conhecidos antes da semana ----------
def stop_romp(px, e=20, x=10):
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
    return alvo, preco


def stop_media(px, n=40):
    c = [p["fech"] for p in px]
    est, alvo, preco = False, [], []
    for i, p in enumerate(px):
        pr = p["fech"]
        if i > n:
            nivel, ab = sum(c[i - n:i]) / n, c[i - 1]  # média até a semana anterior, conhecida no domingo
            if not est and p["alta"] > nivel: est, pr = True, max(nivel, ab)
            elif est and p["baixa"] < nivel: est, pr = False, min(nivel, ab)
        alvo.append(est); preco.append(pr)
    return alvo, preco


def stop_dow(px, w=2):
    c = [p["fech"] for p in px]
    est, alvo, preco, topo, fundo = False, [], [], None, None
    for i, p in enumerate(px):
        pr = p["fech"]
        j = i - 1 - w  # pivôs confirmados até a semana anterior
        if j >= w:
            jan = c[j - w:j + w + 1]
            if c[j] == max(jan): topo = c[j]
            if c[j] == min(jan): fundo = c[j]
        if i > 0:
            ab = c[i - 1]
            if topo is not None and not est and p["alta"] > topo: est, pr = True, max(topo, ab)
            elif fundo is not None and est and p["baixa"] < fundo: est, pr = False, min(fundo, ab)
        alvo.append(est); preco.append(pr)
    return alvo, preco


def stop_pct(px, n=52, lo=20, hi=80):
    """Faixas de percentis: compra quando o preço sobe de volta acima do nível do percentil 20 (estando abaixo);
    vende quando cai de volta abaixo do nível do percentil 80 (estando acima)."""
    c = [p["fech"] for p in px]
    est, alvo, preco = False, [], []
    for i, p in enumerate(px):
        pr = p["fech"]
        if i > n:
            jan = sorted(c[i - n:i])
            n_lo, n_hi = jan[int(len(jan) * lo / 100)], jan[min(len(jan) - 1, int(len(jan) * hi / 100))]
            ab = c[i - 1]
            if not est and ab < n_lo and p["alta"] > n_lo: est, pr = True, max(n_lo, ab)
            elif est and ab > n_hi and p["baixa"] < n_hi: est, pr = False, min(n_hi, ab)
        alvo.append(est); preco.append(pr)
    return alvo, preco


def main():
    px, brl, cdi = ot.carrega()
    datas = [p["data"] for p in px][INI:]
    n = len(datas) - 1
    sin = bt.sinais(px)
    for k in bt.CONSENSOS:
        sin[bt.nome_consenso(k)] = bt.consenso(sin, k)
    fech = [p["fech"] for p in px]
    stops = {"Média de 40 semanas": stop_media(px), "Rompimento 20 semanas": stop_romp(px),
             "Topos e fundos (Dow)": stop_dow(px), "Faixas de percentis 52 semanas": stop_pct(px)}
    cdi_v, _ = simula_exec(px, brl, cdi, [False] * len(px), fech)
    btc_v, _ = simula_exec(px, brl, cdi, [True] * len(px), fech)
    k5 = max(k for k, d in enumerate(datas) if d <= datas[-1].replace(year=datas[-1].year - 5))
    linhas = []
    for nome, s in sin.items():
        if nome == "Comprar e segurar":
            continue
        r = {}
        v1, t1 = simula_exec(px, brl, cdi, [s[0]] + s[:-1], fech)
        v2, t2 = simula_exec(px, brl, cdi, s, fech)
        r["fechamento_seguinte"], r["mesmo_fechamento"] = (v1, t1), (v2, t2)
        if nome in stops:
            r["ordens_no_book"] = simula_exec(px, brl, cdi, *stops[nome])
        m = {}
        for k, (v, t) in r.items():
            tot, cinco = ot.metricas(v, cdi_v, datas, 0, n), ot.metricas(v, cdi_v, datas, k5, n)
            m[k] = {"btc_final": v[-1] / (fech[-1] * brl[-1]), "aa": tot["aa"], "sharpe": tot["sharpe"], "pior_queda": tot["pior_queda"],
                    "aa_5anos": cinco["aa"], "sharpe_5anos": cinco["sharpe"], "operacoes": t}
        linhas.append({"nome": nome, **m})
    bench = {k: {"aa": ot.metricas(v, cdi_v, datas, 0, n)["aa"], "sharpe": ot.metricas(v, cdi_v, datas, 0, n)["sharpe"],
                 "aa_5anos": ot.metricas(v, cdi_v, datas, k5, n)["aa"]} for k, v in (("Bitcoin", btc_v), ("CDI", cdi_v))}
    json.dump({"gerado_em": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "periodo": [datas[0].isoformat(), datas[-1].isoformat()],
               "benchmarks": bench, "estrategias": linhas}, open(os.path.join(AQUI, "execucao.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    p = lambda x: f"{x * 100:6.1f}%"
    print("Benchmarks:", {k: (round(v["aa"] * 100, 1), round(v["sharpe"], 2)) for k, v in bench.items()})
    print(f"{'Estratégia':32} {'premissa':20} {'BTC fim':>7} {'a.a.':>7} {'Sharpe':>6} {'queda':>7} {'5a a.a.':>7} {'oper':>5}")
    for l in linhas:
        for k in ("fechamento_seguinte", "mesmo_fechamento", "ordens_no_book"):
            if k in l:
                m = l[k]
                print(f"{l['nome']:32} {k:20} {m['btc_final']:7.2f} {p(m['aa'])} {m['sharpe']:6.2f} {p(m['pior_queda'])} {p(m['aa_5anos'])} {m['operacoes']:5d}")


if __name__ == "__main__":
    main()
