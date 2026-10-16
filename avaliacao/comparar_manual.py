"""Confronta o resultado do pipeline com a avaliação manual da Sprint 3.

Duas comparações:
  1. Caso a caso: os casos que a Sprint 3 avaliou à mão (Adequado/Inadequado)
     x a taxa de aprovação do pipeline no mesmo caso.
  2. Afirmações: cada conclusão escrita na Sprint 3 (ex.: "100% de resistência a
     injection") é verificada contra a métrica correspondente.

Uso: python -m avaliacao.comparar_manual [pasta_da_execucao]
"""
import json
import sys

from . import config


def _versoes_presentes(res, versoes):
    return [v for v in versoes if v in res["versoes"]]


def comparar_casos(res: dict, manual: dict) -> list[dict]:
    linhas = []
    for item in manual["casos"]:
        for v in _versoes_presentes(res, item["versoes"]):
            taxa = res["versoes"][v]["casos"].get(item["caso"])
            if taxa is None:
                continue
            pipeline = "Adequado" if taxa >= 0.5 else "Inadequado"
            linhas.append({
                "caso": item["caso"], "id_sprint3": item["id_sprint3"], "versao": v,
                "manual": item["avaliacao_manual"], "pipeline": pipeline,
                "taxa_aprovacao": taxa, "concorda": pipeline == item["avaliacao_manual"],
            })
    return linhas


def _fmt(x, pct=False):
    if x is None:
        return "n/d"
    return f"{x:.0%}" if pct else f"{x:.2f}"


def verificar_afirmacao(a: dict, res: dict) -> dict:
    vf = a["verificacao"]
    V = res["versoes"]
    tipo = vf["tipo"]
    if tipo == "metrica_minima":
        vs = _versoes_presentes(res, vf["versoes"])
        if not vs:
            return {"status": "Não verificável", "pipeline": "versões não executadas"}
        valores = {v: V[v]["metricas"][vf["metrica"]] for v in vs}
        ok = [x is not None and x >= vf["valor"] - 1e-9 for x in valores.values()]
        status = "Concorda" if all(ok) else ("Parcial" if any(ok) else "Diverge")
        txt = "; ".join(f"{V[v]['nome']}: {_fmt(x, pct=True)}" for v, x in valores.items())
        return {"status": status, "pipeline": f"{vf['metrica']} = {txt}"}
    if tipo == "caso_reprovado":
        v = vf["versao"]
        if v not in V or vf["caso"] not in V[v]["casos"]:
            return {"status": "Não verificável", "pipeline": "caso/versão não executado"}
        taxa = V[v]["casos"][vf["caso"]]
        status = "Concorda" if taxa < 1 else "Diverge"
        return {"status": status, "pipeline": f"{vf['caso']} na {V[v]['nome']}: aprovação {taxa:.0%}"}
    if tipo == "latencia":
        partes, ok = [], []
        for v, esperado in vf["valores"].items():
            if v not in V or V[v]["metricas"]["latencia_media_s"] is None:
                continue
            medido = V[v]["metricas"]["latencia_media_s"]
            ok.append(abs(medido - esperado) <= vf["tolerancia_relativa"] * esperado)
            partes.append(f"{V[v]['nome']}: {medido:.2f}s (manual ~{esperado}s)")
        if not partes:
            return {"status": "Não verificável", "pipeline": "sem latência medida"}
        status = "Concorda" if all(ok) else ("Parcial" if any(ok) else "Diverge")
        return {"status": status, "pipeline": "; ".join(partes)}
    if tipo in ("comparacao", "comparacao_score"):
        metrica = vf.get("metrica", "score_final")
        a_, b_ = vf["maior"], vf["menor"]
        if a_ not in V or b_ not in V:
            return {"status": "Não verificável", "pipeline": "versões não executadas"}
        xa, xb = V[a_]["metricas"][metrica], V[b_]["metricas"][metrica]
        if xa is None or xb is None:
            return {"status": "Não verificável", "pipeline": f"{metrica} indisponível"}
        empate = vf.get("empate_pontos", 0)
        if xa > xb + empate:
            status = "Concorda"
        elif abs(xa - xb) <= empate:
            status = "Parcial"
        else:
            status = "Diverge"
        nome = "score final" if metrica == "score_final" else metrica
        return {"status": status,
                "pipeline": f"{nome}: {V[a_]['nome']} {xa:.1f} x {V[b_]['nome']} {xb:.1f}"}
    return {"status": "Não verificável", "pipeline": f"tipo {tipo} desconhecido"}


def comparar(res: dict, manual: dict) -> dict:
    afirmacoes = []
    for a in manual["afirmacoes"]:
        r = verificar_afirmacao(a, res)
        afirmacoes.append({**{k: a[k] for k in ("id", "texto", "fonte", "hipoteses_divergencia")}, **r})
    casos = comparar_casos(res, manual)
    return {
        "casos": casos,
        "concordancia_casos": (sum(c["concorda"] for c in casos) / len(casos)) if casos else None,
        "afirmacoes": afirmacoes,
    }


def carregar_execucao(nome: str | None = None) -> tuple[dict, str]:
    if nome is None:
        nome = (config.PASTA_RESULTADOS / "ultima_execucao.txt").read_text(encoding="utf-8").strip()
    pasta = config.PASTA_RESULTADOS / nome
    with open(pasta / "metricas.json", encoding="utf-8") as f:
        return json.load(f), str(pasta)


def main():
    res, pasta = carregar_execucao(sys.argv[1] if len(sys.argv) > 1 else None)
    with open(config.AVALIACAO_MANUAL, encoding="utf-8") as f:
        manual = json.load(f)
    comp = comparar(res, manual)
    print(f"Concordância caso a caso: {_fmt(comp['concordancia_casos'], pct=True)}")
    for a in comp["afirmacoes"]:
        print(f"[{a['status']:<15}] {a['id']} {a['texto']}\n                  pipeline: {a['pipeline']}")


if __name__ == "__main__":
    main()
