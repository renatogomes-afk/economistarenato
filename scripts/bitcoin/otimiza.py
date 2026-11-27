"""Otimização dos sinais do piloto /bitcoin, com retorno corrigido pelo risco e controle de sobreajuste.

Usa os dados gravados pelo backtest (scripts/bitcoin/precos_semanais.json) e as mesmas regras de simula():
decisão semanal; regras com nível de preço (média, rompimento, topos e fundos, faixas de percentis) executam por ordem
no book durante a semana; as demais, no próprio fechamento do sinal; 0,25% por operação, CDI quando fora, valores em reais.

Métrica principal: índice de Sharpe do excesso sobre o CDI (retornos semanais, anualizado por raiz de 52).
Também: Sortino, Calmar (retorno ao ano / pior queda), retorno ao ano e pior queda.

Controle de sobreajuste (otimizar muitos parâmetros sempre acha "o melhor" por sorte):
  1. Dentro x fora da amostra: escolhe o melhor de cada família em jul/2016–dez/2021 e mede em jan/2022–hoje.
  2. Walk-forward: a cada ano, de 2019 em diante, escolhe o melhor parâmetro com os dados até o fim do ano
     anterior e usa só no ano seguinte. A curva encadeada é o que um investidor teria obtido sem ver o futuro.
  3. Platô: a nota de cada parâmetro também considera a mediana dos vizinhos (parâmetro isolado num pico é suspeito).
Saída: scripts/bitcoin/otimizacao.json e um resumo no terminal.
"""
import json, math, os, sys, datetime as dt, statistics as st

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backtest as bt  # noqa: E402

INI = 52
CORTE_OOS = dt.date(2022, 1, 1)
ANO_WF = 2019


def carrega():
    P = json.load(open(os.path.join(AQUI, "precos_semanais.json"), encoding="utf-8"))
    px = [{"data": dt.date.fromisoformat(d), "fech": f, "alta": a, "baixa": b}
          for d, f, a, b in zip(P["datas"], P["fech"], P["alta"], P["baixa"])]
    # fator semanal exato do CDI (gravado pelo backtest); arquivos antigos sem ele caem na aproximação por dias úteis
    juros = P.get("fator_cdi") or [1.0] + [(1 + P["cdi"][k - 1] / 100) ** ((px[k]["data"] - px[k - 1]["data"]).days * 5 / 7)
                                           for k in range(1, len(px))]
    return px, P["ptax"], juros


# ---------- sinais parametrizados (mesma lógica de backtest.sinais, com parâmetros livres) ----------
def s_media(c, n):
    return [bt.sma(c, n, i) is not None and c[i] > bt.sma(c, n, i) for i in range(len(c))]


def s_cruz(c, f, s):
    return [bt.sma(c, s, i) is not None and bt.sma(c, f, i) > bt.sma(c, s, i) for i in range(len(c))]


def s_ifr_rev(c, n, lo, hi):
    r, est, out = bt.rsi_lista(c, n), False, []
    for i in range(len(c)):
        if r[i] is not None and i > 0 and r[i - 1] is not None:
            if not est and r[i - 1] < lo <= r[i]: est = True
            elif est and r[i - 1] > hi >= r[i]: est = False
        out.append(est)
    return out


def s_ifr_mom(c, n, x):
    r = bt.rsi_lista(c, n)
    return [r[i] is not None and r[i] > x for i in range(len(c))]


def s_romp(c, e, x):
    est, out = False, []
    for i in range(len(c)):
        if i >= e:
            if not est and c[i] > max(c[i - e:i]): est = True
            elif est and c[i] < min(c[i - x:i]): est = False
        out.append(est)
    return out


def s_macd(c, f, s, g):
    m = [a - b for a, b in zip(bt.ema_lista(c, f), bt.ema_lista(c, s))]
    sig = bt.ema_lista(m, g)
    return [i >= s + g and m[i] > sig[i] for i in range(len(c))]


def s_dow(c, w):
    est, out, topo, fundo = False, [], None, None
    for i in range(len(c)):
        j = i - w
        if j >= w:
            jan = c[j - w:j + w + 1]
            if c[j] == max(jan): topo = c[j]
            if c[j] == min(jan): fundo = c[j]
        if topo is not None and not est and c[i] > topo: est = True
        elif fundo is not None and est and c[i] < fundo: est = False
        out.append(est)
    return out


def pctl(c, i, n):
    return 100 * sum(1 for x in c[i - n:i] if x < c[i]) / n


def s_pct_rev(c, n, lo, hi):
    est, out, ant = False, [], None
    for i in range(len(c)):
        p = pctl(c, i, n) if i >= n else None
        if p is not None and ant is not None:
            if not est and ant < lo <= p: est = True
            elif est and ant > hi >= p: est = False
        ant = p
        out.append(est)
    return out


def s_pct_mom(c, n, x):
    return [i >= n and pctl(c, i, n) > x for i in range(len(c))]


# regras de nível: ordem no book (devolvem posição e preço de execução)
def b_media(px, n): return bt.book_media(px, n)[:2]
def b_romp(px, e, x): return bt.book_romp(px, e, x)[:2]
def b_dow(px, w): return bt.book_dow(px, w)[:2]
def b_pct(px, n, lo, hi): return bt.book_pct(px, n, lo, hi)[:2]


def grade():
    g = []
    for n in range(10, 62, 2): g.append(("Média móvel", f"preço acima da média de {n} semanas", (n,), b_media))
    for f in range(4, 22, 2):
        for s in range(20, 64, 4):
            if f < s: g.append(("Cruzamento de médias", f"média de {f} acima da de {s} semanas", (f, s), s_cruz))
    for n in (7, 10, 14, 21):
        for lo in (20, 25, 30, 35, 40):
            for hi in (60, 65, 70, 75, 80):
                g.append(("IFR contrário", f"IFR {n}: compra ao subir por {lo}, vende ao cair por {hi}", (n, lo, hi), s_ifr_rev))
        for x in (45, 50, 55, 60):
            g.append(("IFR tendência", f"IFR {n} acima de {x}", (n, x), s_ifr_mom))
    for e in (8, 10, 13, 16, 20, 26, 30, 40, 52):
        for x in (4, 5, 8, 10, 13, 20):
            if x <= e: g.append(("Rompimento", f"compra na máxima de {e} semanas, vende na mínima de {x}", (e, x), b_romp))
    for f in (6, 8, 12, 16):
        for s in (17, 21, 26, 34):
            for sg in (5, 9, 12):
                if f < s: g.append(("MACD", f"MACD {f}/{s}/{sg}", (f, s, sg), s_macd))
    for w in (1, 2, 3, 4, 6): g.append(("Topos e fundos (Dow)", f"pivô de {w} semana(s) de cada lado", (w,), b_dow))
    for n in (26, 52):
        for lo in (10, 20, 30):
            for hi in (70, 80, 90):
                g.append(("Percentis contrário", f"percentil de {n} semanas: compra ao subir por {lo}, vende ao cair por {hi}", (n, lo, hi), b_pct))
        for x in (50, 60, 70, 80):
            g.append(("Percentis tendência", f"percentil de {n} semanas acima de {x}", (n, x), s_pct_mom))
    return g


# ---------- métricas ----------
def metricas(v, cdi_v, datas, a, b):
    """Métricas entre os índices a e b (inclusive) das séries semanais de valor (estratégia e CDI)."""
    r = [v[k] / v[k - 1] - 1 for k in range(a + 1, b + 1)]
    rc = [cdi_v[k] / cdi_v[k - 1] - 1 for k in range(a + 1, b + 1)]
    ex = [x - y for x, y in zip(r, rc)]
    dp = st.pstdev(ex) if len(ex) > 1 else 0
    neg = [min(x, 0) for x in ex]
    dd = math.sqrt(sum(x * x for x in neg) / len(neg)) if neg else 0
    anos = (datas[b] - datas[a]).days / 365.25
    aa = (v[b] / v[a]) ** (1 / anos) - 1
    pico, q = v[a], 0.0
    for k in range(a, b + 1):
        pico = max(pico, v[k]); q = min(q, v[k] / pico - 1)
    return {"sharpe": st.mean(ex) / dp * math.sqrt(52) if dp else 0.0, "sortino": st.mean(ex) / dd * math.sqrt(52) if dd else 0.0,
            "aa": aa, "pior_queda": q, "calmar": aa / -q if q < 0 else 0.0, "vol": st.pstdev(r) * math.sqrt(52)}


def main():
    px, brl, cdi = carrega()
    c = [p["fech"] for p in px]
    datas = [p["data"] for p in px][INI:]
    def roda(sinal, preco=None):
        return bt.simula(px, sinal, brl, cdi, INI, preco)["_valores"]
    cdi_v = roda([False] * len(px))
    btc_v = roda([True] * len(px))
    n = len(datas) - 1
    k_oos = next(k for k, d in enumerate(datas) if d >= CORTE_OOS) - 1  # último domingo de 2021 é a base fora da amostra

    cfgs = []
    for fam, desc, par, fn in grade():
        v = roda(*fn(px, *par)) if fn in (b_media, b_romp, b_dow, b_pct) else roda(fn(c, *par))
        cfgs.append({"familia": fam, "regra": desc, "param": par, "v": v,
                     "dentro": metricas(v, cdi_v, datas, 0, k_oos), "fora": metricas(v, cdi_v, datas, k_oos, n),
                     "total": metricas(v, cdi_v, datas, 0, n)})
    # consensos com os sinais originais
    base = bt.sinais(px)
    for k in (7, 6, 5, 4):
        v = roda(bt.consenso(base, k))
        cfgs.append({"familia": "Consenso dos 7", "regra": f"{k} x {7 - k}", "param": (k,), "v": v,
                     "dentro": metricas(v, cdi_v, datas, 0, k_oos), "fora": metricas(v, cdi_v, datas, k_oos, n),
                     "total": metricas(v, cdi_v, datas, 0, n)})

    # platô: mediana do Sharpe dentro da amostra entre o parâmetro e os vizinhos da mesma família (distância relativa <= 25%)
    for x in cfgs:
        viz = [y["dentro"]["sharpe"] for y in cfgs if y["familia"] == x["familia"] and len(y["param"]) == len(x["param"])
               and all(abs(a - b) <= max(1, 0.25 * abs(a)) for a, b in zip(x["param"], y["param"]))]
        x["plato"] = st.median(viz)

    bench = {"Bitcoin (comprar e segurar)": btc_v, "CDI": cdi_v}
    bench_m = {k: {"dentro": metricas(v, cdi_v, datas, 0, k_oos), "fora": metricas(v, cdi_v, datas, k_oos, n),
                   "total": metricas(v, cdi_v, datas, 0, n)} for k, v in bench.items()}

    # 1. melhor de cada família dentro da amostra (pela nota de platô) e como foi fora
    familias = sorted({x["familia"] for x in cfgs})
    por_familia = []
    for f in familias:
        xs = [x for x in cfgs if x["familia"] == f]
        esc = max(xs, key=lambda x: x["plato"])
        melhor_total = max(xs, key=lambda x: x["total"]["sharpe"])
        por_familia.append({"familia": f, "testadas": len(xs), "escolhida": esc["regra"], "dentro": esc["dentro"], "fora": esc["fora"],
                            "melhor_no_total": melhor_total["regra"], "sharpe_melhor_no_total": melhor_total["total"]["sharpe"],
                            "fracao_positiva_fora": sum(1 for x in xs if x["fora"]["sharpe"] > 0) / len(xs),
                            "mediana_fora": st.median(x["fora"]["sharpe"] for x in xs)})

    # 2. walk-forward por família e geral
    anos = sorted({d.year for d in datas if d.year >= ANO_WF})
    fim_ano = {}
    for k, d in enumerate(datas): fim_ano[d.year] = k
    def walk(xs):
        r, escolhas = [], []
        for a in anos:
            k0 = fim_ano[a - 1]; k1 = fim_ano[a]
            esc = max(xs, key=lambda x: metricas(x["v"], cdi_v, datas, 0, k0)["sharpe"])
            escolhas.append({"ano": a, "familia": esc["familia"], "regra": esc["regra"]})
            r += [esc["v"][k] / esc["v"][k - 1] for k in range(k0 + 1, k1 + 1)]
        v = [1.0]
        for x in r: v.append(v[-1] * x)
        k0 = fim_ano[anos[0] - 1]
        return v, k0, escolhas
    wf = {}
    for f in familias + ["Todas as famílias"]:
        xs = cfgs if f == "Todas as famílias" else [x for x in cfgs if x["familia"] == f]
        v, k0, esc = walk(xs)
        cv = [cdi_v[k] / cdi_v[k0] for k in range(k0, n + 1)]
        wf[f] = {"metricas": metricas(v, cv, datas[k0:], 0, len(v) - 1), "escolhas": esc}
    wf_bench = {k: metricas(v, cdi_v, datas, fim_ano[anos[0] - 1], n) for k, v in bench.items()}

    top_total = sorted(cfgs, key=lambda x: -x["total"]["sharpe"])[:15]
    saida = {"gerado_em": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "testadas": len(cfgs),
             "periodo": [datas[0].isoformat(), datas[-1].isoformat()], "dentro": [datas[0].isoformat(), datas[k_oos].isoformat()],
             "fora": [datas[k_oos].isoformat(), datas[-1].isoformat()], "walk_forward_desde": anos[0],
             "benchmarks": bench_m, "por_familia": por_familia, "walk_forward": wf, "walk_forward_benchmarks": wf_bench,
             "top_total": [{"familia": x["familia"], "regra": x["regra"], "total": x["total"], "dentro": x["dentro"], "fora": x["fora"],
                            "plato": x["plato"]} for x in top_total]}
    json.dump(saida, open(os.path.join(AQUI, "otimizacao.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    f2 = lambda x: f"{x:5.2f}"
    p1 = lambda x: f"{x * 100:6.1f}%"
    print(f"{len(cfgs)} regras testadas. Dentro: {saida['dentro']}; fora: {saida['fora']}.")
    print("\nBenchmarks (Sharpe sobre o CDI): " + "; ".join(f"{k}: dentro {f2(m['dentro']['sharpe'])}, fora {f2(m['fora']['sharpe'])}, total {f2(m['total']['sharpe'])}" for k, m in bench_m.items()))
    print("\nMelhor de cada família (escolhida dentro da amostra, pelo platô) e como foi fora:")
    for x in sorted(por_familia, key=lambda x: -x["fora"]["sharpe"]):
        print(f"  {x['familia']:22} {x['escolhida'][:60]:60} dentro {f2(x['dentro']['sharpe'])} | fora {f2(x['fora']['sharpe'])} {p1(x['fora']['aa'])} a.a. queda {p1(x['fora']['pior_queda'])} | {x['fracao_positiva_fora']:.0%} das regras positivas fora")
    print(f"\nWalk-forward desde {anos[0]} (Sharpe, ao ano, pior queda):")
    for k, m in sorted(wf.items(), key=lambda kv: -kv[1]["metricas"]["sharpe"]):
        mm = m["metricas"]; print(f"  {k:22} {f2(mm['sharpe'])} {p1(mm['aa'])} {p1(mm['pior_queda'])}  calmar {f2(mm['calmar'])}")
    for k, mm in wf_bench.items():
        print(f"  {k:22} {f2(mm['sharpe'])} {p1(mm['aa'])} {p1(mm['pior_queda'])}  calmar {f2(mm['calmar'])}")
    print("\nTop 15 no período todo (Sharpe) — atenção: escolhidos olhando o resultado:")
    for x in top_total:
        print(f"  {x['familia']:22} {x['regra'][:58]:58} total {f2(x['total']['sharpe'])} {p1(x['total']['aa'])} queda {p1(x['total']['pior_queda'])} | dentro {f2(x['dentro']['sharpe'])} fora {f2(x['fora']['sharpe'])}")


if __name__ == "__main__":
    main()
