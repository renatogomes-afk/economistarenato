"""Contexto de mercado do boletim diário: as variáveis que costumam mexer com o bitcoin, a manchete do dia e as
considerações do fechamento, escritas por regras a partir dos números (sem intervenção manual).

Fontes (todas abertas, sem chave):
  - Yahoo Finance, gráfico diário: S&P 500, Nasdaq, índice do dólar (DXY), ouro, juro de 10 anos dos EUA, VIX;
  - Coinbase, velas diárias ETH-USD (UTC);
  - Alternative.me, índice Fear & Greed do cripto;
  - CoinDesk, RSS de notícias (só título e link).
Cada fonte é opcional: se uma falhar, o boletim sai sem ela.
"""
import datetime as dt
import json
import re
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "Mozilla/5.0 (research-client)"}

# (rótulo, símbolo no Yahoo, unidade): "pct" = variação em %, "pb" = variação em pontos-base (juro)
ATIVOS = [("S&P 500", "^GSPC", "pct"), ("Nasdaq", "^IXIC", "pct"), ("Dólar (DXY)", "DX-Y.NYB", "pct"),
          ("Ouro", "GC=F", "pct"), ("Juro de 10 anos dos EUA", "^TNX", "pb"), ("VIX (medo na bolsa)", "^VIX", "pct")]

FG_PT = {"Extreme Fear": "medo extremo", "Fear": "medo", "Neutral": "neutro", "Greed": "ganância", "Extreme Greed": "ganância extrema"}


def _get(url, tentativas=3):
    import time
    for t in range(tentativas):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
                return r.read()
        except Exception:
            if t == tentativas - 1:
                raise
            time.sleep(3 * (t + 1))


def yahoo(simbolo, D):
    """Fechamento (ou último preço, se o pregão de D ainda corre) do dia D na data local da bolsa, e o anterior."""
    j = json.loads(_get(f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.request.quote(simbolo)}?interval=1d&range=15d"))
    r = j["chart"]["result"][0]
    off = r["meta"].get("gmtoffset", 0)
    fech = {}
    for ts, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]):
        if c is not None:
            fech[dt.datetime.fromtimestamp(ts + off, dt.timezone.utc).date()] = float(c)
    if D not in fech:
        return {"aberto": False}
    ant = [d for d in fech if d < D]
    if not ant:
        return {"aberto": False}
    return {"aberto": True, "valor": fech[D], "anterior": fech[max(ant)]}


def eth(D):
    url = (f"https://api.exchange.coinbase.com/products/ETH-USD/candles?granularity=86400"
           f"&start={(D - dt.timedelta(days=3)).isoformat()}T00:00:00Z&end={D.isoformat()}T23:59:59Z")
    v = {dt.datetime.fromtimestamp(int(t), dt.timezone.utc).date(): float(c) for t, lo, hi, op, c, vol in json.loads(_get(url))}
    return {"aberto": True, "valor": v[D], "anterior": v[D - dt.timedelta(days=1)]}


def medo_ganancia(D):
    j = json.loads(_get("https://api.alternative.me/fng/?limit=10"))
    for x in j["data"]:
        if dt.datetime.fromtimestamp(int(x["timestamp"]), dt.timezone.utc).date() == D:
            return {"valor": int(x["value"]), "classe": FG_PT.get(x["value_classification"], x["value_classification"])}
    return None


def manchetes(D, n=5):
    raiz = ET.fromstring(_get("https://www.coindesk.com/arc/outboundfeeds/rss/"))
    out = []
    for it in raiz.iter("item"):
        try:
            quando = dt.datetime.strptime(re.sub(r"\s+", " ", it.findtext("pubDate").strip()), "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            continue
        if quando.astimezone(dt.timezone.utc).date() == D:
            out.append({"titulo": it.findtext("title").strip(), "link": it.findtext("link").strip()})
    return out[:n]


def contexto(D):
    """Variáveis do dia D (UTC). Cada item: rotulo, unidade, aberto, valor, anterior. Fontes que falham ficam de fora."""
    vars_, erros = [], []
    for rot, sim, un in ATIVOS:
        try:
            vars_.append({"rotulo": rot, "simbolo": sim, "unidade": un, **yahoo(sim, D)})
        except Exception as ex:
            erros.append(f"{sim}: {ex.__class__.__name__}")
    try:
        vars_.append({"rotulo": "Ether (ETH)", "simbolo": "ETH-USD", "unidade": "pct", **eth(D)})
    except Exception as ex:
        erros.append(f"ETH: {ex.__class__.__name__}")
    out = {"variaveis": vars_, "erros": erros}
    try:
        out["medo_ganancia"] = medo_ganancia(D)
    except Exception as ex:
        erros.append(f"fng: {ex.__class__.__name__}")
    try:
        out["manchetes"] = manchetes(D)
    except Exception as ex:
        erros.append(f"rss: {ex.__class__.__name__}")
    return out


def variacao(v):
    """Variação em % (fração) ou em pontos-base, conforme a unidade; None se o mercado não abriu."""
    if not v.get("aberto"):
        return None
    if v["unidade"] == "pb":
        k = 100 if v["valor"] < 20 else 10  # o Yahoo já cotou o ^TNX em % e em décimos de %
        return (v["valor"] - v["anterior"]) * k
    return v["valor"] / v["anterior"] - 1


def _p(x):
    return f"{abs(x) * 100:.1f}%".replace(".", ",")


def consideracoes(B):
    """Considerações do fechamento, por regras simples sobre os números do boletim. Lista de frases."""
    u, m, ab = B["btc_usd"], B.get("mercado") or {}, B.get("abertura")
    vs = {v["simbolo"]: v for v in m.get("variaveis", [])}
    out = []
    r = u["fech"] / u["ontem"] - 1 if u.get("ontem") else None
    if r is not None:
        out.append(f"Dia de pouca variação: o bitcoin fechou {'em alta' if r >= 0 else 'em baixa'} de {_p(r)}." if abs(r) < 0.01
                   else f"O bitcoin {'subiu' if r > 0 else 'caiu'} {_p(r)} no dia, entre US$ {u['baixa']:,.0f} e US$ {u['alta']:,.0f}.".replace(",", "."))
    if ab and u.get("ontem"):
        pre, pos = ab["btc_usd"] / u["ontem"] - 1, u["fech"] / ab["btc_usd"] - 1
        hora = ab["hora_cuiaba"]
        if abs(pre) + abs(pos) > 0.005:
            quem = "na sessão americana, depois da abertura de Nova York" if abs(pos) > abs(pre) else "antes da abertura de Nova York, com a Ásia e a Europa"
            out.append(f"Até o boletim de abertura ({hora} em Cuiabá) o bitcoin {'subia' if pre >= 0 else 'caía'} {_p(pre)}; dali ao fechamento, "
                       f"{'subiu' if pos >= 0 else 'caiu'} mais {_p(pos)}. A maior parte do movimento veio {quem}." if (pre >= 0) == (pos >= 0) else
                       f"Até o boletim de abertura ({hora} em Cuiabá) o bitcoin {'subia' if pre >= 0 else 'caía'} {_p(pre)}; dali ao fechamento, "
                       f"{'subiu' if pos >= 0 else 'caiu'} {_p(pos)}, devolvendo {'parte' if abs(pos) < abs(pre) else 'tudo'} do movimento da manhã.")
    nq = vs.get("^IXIC")
    if nq is not None and r is not None:
        rn = variacao(nq)
        if rn is None:
            out.append("As bolsas americanas não abriram (fim de semana ou feriado): o movimento do dia veio do próprio mercado de cripto.")
        elif abs(rn) >= 0.005 and abs(r) >= 0.005:
            out.append(f"O bitcoin {'acompanhou as' if (rn > 0) == (r > 0) else 'andou na contramão das'} bolsas americanas: a Nasdaq {'subiu' if rn > 0 else 'caiu'} {_p(rn)}.")
        elif abs(rn) < 0.005:
            out.append(f"Bolsas americanas de lado (Nasdaq {'+' if rn >= 0 else '−'}{_p(rn)}): o movimento do bitcoin teve causa própria.")
    dx = vs.get("DX-Y.NYB")
    rd = variacao(dx) if dx else None
    if rd is not None and abs(rd) >= 0.003:
        extra = " Dólar forte costuma pesar sobre o bitcoin." if rd > 0 and r is not None and r < 0 else (" Dólar fraco costuma ajudar o bitcoin." if rd < 0 and r is not None and r > 0 else "")
        out.append(f"O índice do dólar (DXY) {'subiu' if rd > 0 else 'caiu'} {_p(rd)}.{extra}")
    tn = vs.get("^TNX")
    pb = variacao(tn) if tn else None
    if pb is not None and abs(pb) >= 5:
        out.append(f"O juro do título de 10 anos dos EUA {'subiu' if pb > 0 else 'caiu'} {abs(pb):.0f} pontos-base: juro {'mais alto encarece' if pb > 0 else 'mais baixo alivia'} os ativos de risco.")
    vx = vs.get("^VIX")
    rv = variacao(vx) if vx else None
    if rv is not None and abs(rv) >= 0.08:
        out.append(f"O VIX, o termômetro de medo da bolsa americana, {'subiu' if rv > 0 else 'caiu'} {_p(rv)}: {'mais' if rv > 0 else 'menos'} aversão a risco.")
    au = vs.get("GC=F")
    ra = variacao(au) if au else None
    if ra is not None and abs(ra) >= 0.01:
        out.append(f"O ouro {'subiu' if ra > 0 else 'caiu'} {_p(ra)}.")
    et = vs.get("ETH-USD")
    re_ = variacao(et) if et else None
    if re_ is not None and r is not None and abs(re_ - r) >= 0.02:
        out.append(f"O ether {'subiu' if re_ > 0 else 'caiu'} {_p(re_)}, {'melhor' if re_ > r else 'pior'} que o bitcoin: {'apetite maior' if re_ > r else 'fuga'} para o risco dentro do cripto.")
    fg = m.get("medo_ganancia")
    if fg:
        out.append(f"O índice Fear & Greed do cripto marcava {fg['valor']} de 100 ({fg['classe']}).")
    acion = [x for x in B["estrategias"] if x["book"] and x["mudou"]]
    if acion:
        out.append("Ordens no book acionadas na semana: " + "; ".join(f"{x['nome']} ({'compra' if x['agora'] else 'venda'} a US$ {x['acionada_usd']:,.0f})".replace(",", ".") for x in acion) + ".")
    if B["votos_agora"] != B["votos_domingo"]:
        out.append(f"O placar dos sete sinais passou de {B['votos_domingo']} para {B['votos_agora']} de 7 desde domingo.")
    return out
