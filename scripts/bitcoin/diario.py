"""Boletim diário do piloto /bitcoin.

Roda todo dia às 00:10 UTC (20:10 em Cuiabá), logo depois do fechamento do dia na Coinbase (meia-noite UTC).
Grava scripts/bitcoin/diarios/AAAA-MM-DD.json do dia que acabou de fechar, uma vez só, nunca reescrito.

As estratégias continuam semanais. O boletim diário mostra como a semana em curso está andando:
  - o preço do dia e da semana até ali;
  - as ordens no book que já foram acionadas na semana (regras de nível), que valem como operação feita;
  - o que as regras de fechamento (cruzamento, IFR, MACD e consensos) decidiriam se a semana fechasse naquele dia.

Boletim de abertura: uma hora depois da abertura da bolsa de Nova York (10h30 em Nova York; 11h30 em Cuiabá no horário
de inverno americano, 10h30 no de verão), grava scripts/bitcoin/diarios/abertura/AAAA-MM-DD.json com o dia até ali e o
contexto de mercado. O boletim de fechamento registra esse retrato e conclui com as considerações do dia
(scripts/bitcoin/mercado.py): as variáveis que mexeram com o mercado e as manchetes.

Rodado à mão (workflow_dispatch), também grava scripts/bitcoin/diarios/parcial.json com o dia em curso até a hora
da execução, marcado como parcial; o boletim fechado do dia substitui a prévia na página à noite.
"""
import json, os, sys, datetime as dt
from zoneinfo import ZoneInfo

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backtest as bt  # noqa: E402
import mercado  # noqa: E402

PASTA = os.path.join(AQUI, "diarios")
PASTA_AB = os.path.join(PASTA, "abertura")
NY, CUIABA = ZoneInfo("America/New_York"), ZoneInfo("America/Cuiaba")


def semanas_ate(dias, ate):
    """Semanas que fecham no domingo, com a última possivelmente parcial (termina no dia `ate`)."""
    semanas = {}
    for d in sorted(x for x in dias if x <= ate):
        domingo = d + dt.timedelta(days=6 - d.weekday())
        hi, lo, cl = dias[d]
        w = semanas.setdefault(domingo, {"data": domingo, "alta": hi, "baixa": lo, "fech": cl, "ult": d})
        w["alta"], w["baixa"], w["fech"], w["ult"] = max(w["alta"], hi), min(w["baixa"], lo), cl, d
    return [w for _, w in sorted(semanas.items())]


def boletim(dias, D, parcial=False):
    px = semanas_ate(dias, D)
    n = len(px) - 1
    sin = bt.sinais(px)
    for k in bt.CONSENSOS:
        sin[bt.nome_consenso(k)] = bt.consenso(sin, k)
    ordens = {nome: f(px[:-1])[2] for nome, f in bt.BOOK.items()}  # níveis conhecidos no domingo
    precos = {nome: f(px)[1] for nome, f in bt.BOOK.items()}
    hi, lo, cl = dias[D]
    ontem = dias.get(D - dt.timedelta(days=1))
    est = []
    for nome, s in sin.items():
        if nome == "Comprar e segurar":
            continue
        antes, agora = bool(s[n - 1]), bool(s[n])
        livro = nome in bt.BOOK
        o = ordens.get(nome)
        est.append({"nome": nome, "domingo": antes, "agora": agora, "mudou": antes != agora, "book": livro,
                    "acionada_usd": round(precos[nome][n], 2) if livro and antes != agora else None,
                    "ordem": {"tipo": o[0], "nivel_usd": round(o[1], 2)} if o and o[1] is not None else None})
    return {"data": D.isoformat(), "parcial": parcial,
            "gerado_em": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "domingo": px[n - 1]["data"].isoformat(),
            "btc_usd": {"fech": cl, "alta": hi, "baixa": lo, "ontem": ontem[2] if ontem else None,
                        "domingo": px[n - 1]["fech"], "alta_semana": px[n]["alta"], "baixa_semana": px[n]["baixa"]},
            "votos_domingo": sum(sin[v][n - 1] for v in bt.VOTANTES), "votos_agora": sum(sin[v][n] for v in bt.VOTANTES),
            "estrategias": est}


def hora_cuiaba(agora):
    return agora.astimezone(CUIABA).strftime("%Hh%M")


def resumo_abertura(A):
    return {"hora_utc": A["gerado_em"], "hora_cuiaba": A["hora_cuiaba"], "btc_usd": A["btc_usd"]["fech"],
            "alta": A["btc_usd"]["alta"], "baixa": A["btc_usd"]["baixa"], "votos": A["votos_agora"],
            "acionadas": [x["nome"] for x in A["estrategias"] if x["book"] and x["mudou"]]}


def fechamento(dias, D):
    B = boletim(dias, D)
    arq_ab = os.path.join(PASTA_AB, f"{D.isoformat()}.json")
    if os.path.exists(arq_ab):
        B["abertura"] = resumo_abertura(json.load(open(arq_ab, encoding="utf-8")))
    B["mercado"] = mercado.contexto(D)
    B["consideracoes"] = mercado.consideracoes(B)
    return B


def main():
    _, dias = bt.btc_semanal()
    os.makedirs(PASTA_AB, exist_ok=True)
    agora = dt.datetime.now(dt.timezone.utc)
    hoje = agora.date()
    D = hoje - dt.timedelta(days=1)  # último dia fechado (UTC)
    arq = os.path.join(PASTA, f"{D.isoformat()}.json")
    if D in dias and not os.path.exists(arq):
        json.dump(fechamento(dias, D), open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("gravado", arq)
    # abertura: de 1h a 4h depois da abertura de Nova York (9h30 locais), uma vez por dia
    ny = agora.astimezone(NY)
    alvo = ny.replace(hour=10, minute=30, second=0, microsecond=0)
    arq_ab = os.path.join(PASTA_AB, f"{hoje.isoformat()}.json")
    if (alvo <= ny <= alvo + dt.timedelta(hours=3) or os.environ.get("ABERTURA") == "1") and hoje in dias and not os.path.exists(arq_ab):
        A = boletim(dias, hoje, parcial=True)
        A["hora_cuiaba"] = hora_cuiaba(agora)
        A["mercado"] = mercado.contexto(hoje)
        json.dump(A, open(arq_ab, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("gravada a abertura de", hoje, A["mercado"].get("erros"))
    if os.environ.get("PARCIAL") == "1" and hoje in dias:
        P = boletim(dias, hoje, parcial=True)
        if os.path.exists(arq_ab):
            P["abertura"] = resumo_abertura(json.load(open(arq_ab, encoding="utf-8")))
        json.dump(P, open(os.path.join(PASTA, "parcial.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("gravada a prévia de", hoje)
    if os.environ.get("TESTE_MERCADO") == "1":  # só confere as fontes, sem gravar
        T = fechamento(dias, D)
        print(json.dumps({k: T[k] for k in ("mercado", "consideracoes")}, ensure_ascii=False, indent=1))
    # a prévia some quando o dia dela já tem boletim fechado
    p = os.path.join(PASTA, "parcial.json")
    if os.path.exists(p) and os.path.exists(os.path.join(PASTA, json.load(open(p, encoding="utf-8"))["data"] + ".json")):
        os.remove(p)


if __name__ == "__main__":
    main()
