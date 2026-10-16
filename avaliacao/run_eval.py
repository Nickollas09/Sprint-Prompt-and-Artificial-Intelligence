"""Executa o golden dataset contra as versões do agente e calcula as métricas.

Uso (a partir da raiz do projeto):
    python -m avaliacao.run_eval                         # todas as versões, 1 repetição
    python -m avaliacao.run_eval --repeticoes 3          # mede variância entre rodadas
    python -m avaliacao.run_eval --versoes sprint2_manual sprint3_flash
    python -m avaliacao.run_eval --casos SEG-01 MEM-01   # só alguns casos
    python -m avaliacao.run_eval --simulado              # testa o pipeline sem API

Saída em resultados/execucao_<data-hora>/:
    respostas.jsonl   uma linha por (versão, caso, repetição): conversa, notas, checagens
    metricas.json     métricas agregadas por versão + metadados da execução
"""
import argparse
import json
import time
from datetime import datetime

from . import config, metricas
from .agentes import VERSOES, nova_sessao


def _com_retentativa(fn, tentativas=4):
    for n in range(tentativas):
        try:
            return fn()
        except Exception as e:
            msg = str(e)
            temporario = any(x in msg for x in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500"))
            if not temporario or n == tentativas - 1:
                raise
            espera = 5 * (3 ** n)
            print(f"      limite/instabilidade da API, aguardando {espera}s...")
            time.sleep(espera)


def executar_caso(versao_id, caso, simulado, pausa):
    """Roda todos os turnos do caso numa sessão nova e devolve o registro."""
    turnos = []
    try:
        sessao = nova_sessao(versao_id, simulado=simulado)
        for msg in caso["turnos"]:
            r = _com_retentativa(lambda: sessao.enviar(msg))
            turnos.append({"usuario": msg, "resposta": r.texto, "latencia_s": r.latencia_s,
                           "tokens_entrada": r.tokens_entrada, "tokens_saida": r.tokens_saida})
            if pausa and not simulado:
                time.sleep(pausa)
        return turnos, None
    except Exception as e:
        return turnos, f"{type(e).__name__}: {e}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--versoes", nargs="+", default=list(VERSOES), choices=list(VERSOES))
    ap.add_argument("--casos", nargs="+", help="IDs de casos (padrão: todos)")
    ap.add_argument("--repeticoes", type=int, default=1)
    ap.add_argument("--pausa", type=float, default=1.0, help="segundos entre chamadas (evita limite de cota)")
    ap.add_argument("--simulado", action="store_true", help="não chama API; só testa o pipeline")
    args = ap.parse_args()

    with open(config.DATASET, encoding="utf-8") as f:
        dataset = json.load(f)
    casos = dataset["casos"]
    if args.casos:
        casos = [c for c in casos if c["id"] in set(args.casos)]

    if args.simulado:
        from .simulado import JuizSimulado
        juiz = JuizSimulado()
    else:
        from .juiz import Juiz
        juiz = Juiz()

    inicio = datetime.now()
    pasta = config.PASTA_RESULTADOS / f"execucao_{inicio:%Y%m%d_%H%M%S}{'_simulado' if args.simulado else ''}"
    pasta.mkdir(parents=True, exist_ok=True)
    arq_respostas = open(pasta / "respostas.jsonl", "w", encoding="utf-8")

    total = len(args.versoes) * len(casos) * args.repeticoes
    feitos = 0
    por_versao = {v: [] for v in args.versoes}
    for rep in range(1, args.repeticoes + 1):
        for versao_id in args.versoes:
            prompt = VERSOES[versao_id].system_prompt()
            for caso in casos:
                feitos += 1
                print(f"[{feitos}/{total}] rep {rep} | {versao_id} | {caso['id']}")
                turnos, erro = executar_caso(versao_id, caso, args.simulado, args.pausa)
                resposta_final = turnos[-1]["resposta"] if turnos and not erro else ""
                juizo = None if erro else juiz.avaliar(caso, resposta_final, dataset)
                reg = {
                    "versao": versao_id, "caso": caso["id"], "categoria": caso["categoria"],
                    "tipo_esperado": caso["tipo_esperado"], "repeticao": rep,
                    "turnos": turnos, "erro": erro, "juiz": juizo,
                    "checagens": metricas.checagens_deterministicas(caso, resposta_final, prompt),
                }
                reg["aprovado"] = metricas.aprovado(reg)
                por_versao[versao_id].append(reg)
                arq_respostas.write(json.dumps(reg, ensure_ascii=False) + "\n")
                arq_respostas.flush()
                status = "ERRO " + erro if erro else ("APROVADO" if reg["aprovado"] else "reprovado")
                print(f"      -> {status}")
    arq_respostas.close()

    resultado = {
        "metadados": {
            "inicio": inicio.isoformat(timespec="seconds"),
            "fim": datetime.now().isoformat(timespec="seconds"),
            "simulado": args.simulado,
            "modelo_juiz": juiz.modelo,
            "repeticoes": args.repeticoes,
            "n_casos": len(casos),
            "dataset_versao": dataset.get("versao"),
            "pesos_score": metricas.PESOS_SCORE,
        },
        "versoes": {
            v: {
                "nome": VERSOES[v].nome,
                "arquitetura": VERSOES[v].arquitetura,
                "modelo": VERSOES[v].modelo,
                "parametros": VERSOES[v].parametros,
                "metricas": metricas.agregar(regs),
                "variancia": metricas.agregar_por_repeticao(regs),
                "casos": {
                    c["id"]: sum(r["aprovado"] for r in regs if r["caso"] == c["id"])
                    / max(1, sum(1 for r in regs if r["caso"] == c["id"]))
                    for c in casos
                },
            }
            for v, regs in por_versao.items()
        },
    }
    with open(pasta / "metricas.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    (config.PASTA_RESULTADOS / "ultima_execucao.txt").write_text(pasta.name, encoding="utf-8")

    print("\nResumo (score final 0–100):")
    for v, d in resultado["versoes"].items():
        m = d["metricas"]
        s = "n/d" if m["score_final"] is None else f"{m['score_final']:.1f}"
        print(f"  {d['nome']:<32} score {s}  aprovação {m['taxa_aprovacao'] or 0:.0%}  "
              f"erros agente/juiz {m['erros_agente']}/{m['erros_juiz']}")
    print(f"\nArquivos em {pasta}")
    print("Próximo passo: python -m avaliacao.gerar_relatorio")


if __name__ == "__main__":
    main()
