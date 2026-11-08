"""Importa resenhas de capítulos (e, opcionalmente, a ficha do livro) para scripts/leituras/<livro>.json.

Uso: python scripts/leituras/importa_leitura.py <livro-slug> <pasta_com_jsons>
- livro.json (opcional) atualiza a ficha, as partes e a lista de capítulos; as resenhas existentes são mantidas.
- capNN.json: cada resenha substitui (ou acrescenta) a de mesmo número. Resenhas em ordem, sem lacunas, a partir do 1.
- A lista de verificação de fatos vai para scripts/leituras/_verificacao.json (não é publicada).
"""
import json, os, sys, glob, re

AQUI = os.path.dirname(os.path.abspath(__file__))
LIVRO, ORIGEM = sys.argv[1], sys.argv[2]
ARQ = os.path.join(AQUI, f"{LIVRO}.json")
dados = json.load(open(ARQ, encoding="utf-8")) if os.path.exists(ARQ) else {"slug": LIVRO, "resenhas": []}
vpath = os.path.join(AQUI, "_verificacao.json")
verif = json.load(open(vpath, encoding="utf-8")) if os.path.exists(vpath) else {}

OBRIG = ["slug", "numero", "titulo", "titulo_original", "paginas", "chamada", "blocos", "hoje"]
TIPOS = {"p", "h2", "caixa", "citacao", "leitura"}

lf = os.path.join(ORIGEM, "livro.json")
if os.path.exists(lf):
    L = json.load(open(lf, encoding="utf-8"))
    verif[f"{LIVRO}:livro"] = L.pop("verificacao", [])
    resenhas = dados.get("resenhas", [])
    dados.update(L)
    dados["slug"], dados["resenhas"] = LIVRO, resenhas
    print("ficha do livro atualizada")

por_num = {r["numero"]: r for r in dados.get("resenhas", [])}
for f in sorted(glob.glob(os.path.join(ORIGEM, "cap*.json"))):
    r = json.load(open(f, encoding="utf-8"))
    faltam = [k for k in OBRIG if k not in r]
    assert not faltam, f"{f}: faltam {faltam}"
    assert re.fullmatch(r"cap-\d{2,3}-[a-z0-9-]+", r["slug"]), f"{f}: slug inválido {r['slug']}"
    for b in r["blocos"]:
        assert b.get("tipo") in TIPOS, f"{f}: bloco inválido {b}"
        if b["tipo"] == "citacao":
            assert len(b.get("original", "").split()) <= 32, f"{f}: citação longa demais: {b['original'][:60]}"
    assert sum(b["tipo"] == "citacao" for b in r["blocos"]) <= 3, f"{f}: mais de 3 citações"
    assert "WGSA" not in json.dumps(r, ensure_ascii=False), f"{f}: menciona WGSA"
    h = r["hoje"].strip()
    for pre in ("E hoje?", "E hoje:"):
        if h.startswith(pre): h = h[len(pre):].strip()
    r["hoje"] = h
    r.pop("resumo_hub", None)
    verif[f"{LIVRO}:{r['slug']}"] = r.pop("verificacao", [])
    por_num[r["numero"]] = r
    print("importada", r["numero"], r["slug"])

dados["resenhas"] = [por_num[k] for k in sorted(por_num)]
nums = [r["numero"] for r in dados["resenhas"]]
assert nums == list(range(1, len(nums) + 1)), f"numeração com lacuna: {nums}"
json.dump(dados, open(ARQ, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
json.dump(verif, open(vpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("resenhas:", nums)
