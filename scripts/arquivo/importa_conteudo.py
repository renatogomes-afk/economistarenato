"""Importa textos revisados (JSON por edição + notas.json) para scripts/arquivo/edicoes.json e notas.json.

Uso: python scripts/arquivo/importa_conteudo.py <pasta_com_jsons>
- Cada <slug>.json substitui (ou acrescenta) a edição com o mesmo slug; ordena por número.
- A lista de verificação de fatos de cada texto vai para scripts/arquivo/verificacao.json (não é publicada).
"""
import json, os, sys, glob, re

AQUI = os.path.dirname(os.path.abspath(__file__))
ORIGEM = sys.argv[1]
EDS = os.path.join(AQUI, "edicoes.json")
dados = json.load(open(EDS, encoding="utf-8"))
verif_path = os.path.join(AQUI, "verificacao.json")
verif = json.load(open(verif_path, encoding="utf-8")) if os.path.exists(verif_path) else {}

OBRIG = ["slug", "numero", "titulo", "titulo_original", "autores", "publicacao", "volume", "data", "chamada", "blocos", "hoje", "itens", "jstor_edicao"]
TIPOS = {"p", "h2", "caixa", "citacao", "leitura", "comentario"}

por_slug = {e["slug"]: e for e in dados["edicoes"]}
for f in sorted(glob.glob(os.path.join(ORIGEM, "*.json"))):
    if os.path.basename(f) == "notas.json":
        continue
    ed = json.load(open(f, encoding="utf-8"))
    faltam = [k for k in OBRIG if k not in ed]
    assert not faltam, f"{f}: faltam {faltam}"
    for b in ed["blocos"]:
        assert b.get("tipo") in TIPOS, f"{f}: bloco inválido {b}"
    assert any(b["tipo"] == "leitura" for b in ed["blocos"]), f"{f}: sem 'Na minha leitura'"
    assert "WGSA" not in json.dumps(ed, ensure_ascii=False), f"{f}: menciona WGSA"
    h = ed["hoje"].strip()
    for pre in ("E hoje?", "E hoje:"):
        if h.startswith(pre): h = h[len(pre):].strip()
    ed["hoje"] = h
    verif[ed["slug"]] = ed.pop("verificacao", [])
    slugs_art = {x.get("ensaio_slug") for x in ed.get("artigos", [])}
    if ed.get("publicacao") == "The American Economic Review":
        # Piso de conteúdo (decisão do dono, 14/11/2026): todo artigo principal explica ideia e argumento no hub.
        reuniao = "suplemento" in ed.get("volume", "")
        orig = {i[2]: i[0] for i in ed["itens"]}
        # Formato de 14/11/2026: cada artigo principal é uma seção da resenha (h2 com "artigo": jstor).
        secoes, atual = {}, None
        for bl in ed["blocos"]:
            if bl["tipo"] == "h2":
                atual = bl.get("artigo")
                if atual: secoes[atual] = 0
                continue
            if atual:
                txt = bl.get("texto", "")
                secoes[atual] += len((" ".join(txt) if isinstance(txt, list) else txt).split())
        for x in ed.get("artigos", []):
            t0 = orig.get(x.get("jstor"), "")
            if t0.startswith(("[untitled]", "New Book")) or re.search(r"Documents|Periodicals|^Notes|List of Doctoral|Communication|Personal and Miscellaneous|Back Matter|^Purposes of|^Constitution of|List of Members|Program|Doctoral Dissertations|Geographical Index|^Book Reviews|^Correspondence|^Index of|^Books Reviewed|^Publications of the American Economic|^\[[^\]]*\]$|^\[.*\]: ", t0):
                continue
            n = len(x.get("resumo", "").split())
            if secoes:
                n = secoes.get(x.get("jstor"), 0)
            discussao = re.search(r"Discussion|Round Table|Meeting|Address of|Luncheon", t0)
            piso = 0 if (reuniao and discussao) else (150 if reuniao else 300)
            assert n >= piso, f"{f}: artigo {x.get('jstor')} '{t0[:50]}' com {n} palavras (< {piso})"
    for c in ed.get("comentarios", []):
        for k in ("slug", "titulo", "titulo_original", "autores", "paginas", "jstor", "chamada", "blocos", "hoje"):
            assert k in c, f"{f}: comentário sem {k}"
        for bl in c["blocos"]:
            assert bl.get("tipo") in TIPOS, f"{f}: bloco inválido {bl}"
        assert any(bl["tipo"] == "leitura" for bl in c["blocos"]), f"{f}: comentário {c['slug']} sem 'Na minha leitura'"
        assert c["slug"] in slugs_art, f"{f}: comentário {c['slug']} sem ensaio_slug correspondente em artigos"
        verif[ed["slug"] + "/" + c["slug"]] = c.pop("verificacao", [])
    por_slug[ed["slug"]] = ed
    print("importada", ed["numero"], ed["slug"])

dados["edicoes"] = sorted(por_slug.values(), key=lambda e: e["numero"])
nums = [e["numero"] for e in dados["edicoes"]]
assert nums == list(range(1, len(nums) + 1)), f"numeração com lacuna: {nums}"
json.dump(dados, open(EDS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

nf = os.path.join(ORIGEM, "notas.json")
if os.path.exists(nf):
    notas = json.load(open(nf, encoding="utf-8"))
    for n in notas["notas"]:
        verif["nota:" + n["slug"]] = n.pop("verificacao", [])
    json.dump(notas, open(os.path.join(AQUI, "notas.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("notas:", [n["slug"] for n in notas["notas"]])

json.dump(verif, open(verif_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("edições:", nums)
