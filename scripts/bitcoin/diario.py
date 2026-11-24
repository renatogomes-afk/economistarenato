"""Boletim diário do piloto /bitcoin.

Roda todo dia às 00:10 UTC (20:10 em Cuiabá), logo depois do fechamento do dia na Coinbase (meia-noite UTC).
Grava scripts/bitcoin/diarios/AAAA-MM-DD.json do dia que acabou de fechar, uma vez só, nunca reescrito.

As estratégias continuam semanais. O boletim diário mostra como a semana em curso está andando:
  - o preço do dia e da semana até ali;
  - as ordens no book que já foram acionadas na semana (regras de nível), que valem como operação feita;
  - o que as regras de fechamento (cruzamento, IFR, MACD e consensos) decidiriam se a semana fechasse naquele dia.

Rodado à mão (workflow_dispatch), também grava scripts/bitcoin/diarios/parcial.json com o dia em curso até a hora
da execução, marcado como parcial; o boletim fechado do dia substitui a prévia na página à noite.
"""
import json, os, sys, datetime as dt

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import backtest as bt  # noqa: E402

PASTA = os.path.join(AQUI, "diarios")


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


def main():
    _, dias = bt.btc_semanal()
    os.makedirs(PASTA, exist_ok=True)
    hoje = dt.datetime.now(dt.timezone.utc).date()
    D = hoje - dt.timedelta(days=1)  # último dia fechado (UTC)
    arq = os.path.join(PASTA, f"{D.isoformat()}.json")
    if D in dias and not os.path.exists(arq):
        json.dump(boletim(dias, D), open(arq, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("gravado", arq)
    if os.environ.get("PARCIAL") == "1" and hoje in dias:
        json.dump(boletim(dias, hoje, parcial=True), open(os.path.join(PASTA, "parcial.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("gravada a prévia de", hoje)
    # a prévia some quando o dia dela já tem boletim fechado
    p = os.path.join(PASTA, "parcial.json")
    if os.path.exists(p) and os.path.exists(os.path.join(PASTA, json.load(open(p, encoding="utf-8"))["data"] + ".json")):
        os.remove(p)


if __name__ == "__main__":
    main()
