"""Modo SIMULADO: agentes e juiz falsos, sem chamar nenhuma API.

Serve só para testar se o pipeline roda de ponta a ponta (sem gastar cota).
Os números produzidos aqui NÃO são resultados do agente e não devem ir para o
relatório. O relatório gerado a partir de uma execução simulada recebe um aviso.
"""
import hashlib
import json
import random

from .agentes import Resposta
from . import config

with open(config.DATASET, encoding="utf-8") as _f:
    _CASOS = {c["turnos"][-1]: c for c in json.load(_f)["casos"]}

# Probabilidade (fictícia) de cada versão simulada acertar, por categoria.
_PERFIL = {
    "sprint2_manual": {"funcional": 0.9, "memoria": 0.7, "seguranca": 0.4, "escopo": 0.8,
                       "profissional": 0.5, "alucinacao": 0.5, "borda": 0.7},
    "sprint3_flash": {"funcional": 0.5, "memoria": 0.9, "seguranca": 0.9, "escopo": 0.9,
                      "profissional": 0.9, "alucinacao": 0.8, "borda": 0.6},
    "sprint3_pro": {"funcional": 0.6, "memoria": 0.95, "seguranca": 0.95, "escopo": 0.9,
                    "profissional": 0.9, "alucinacao": 0.85, "borda": 0.7},
}


def _rng(*partes) -> random.Random:
    semente = hashlib.sha256("|".join(map(str, partes)).encode()).hexdigest()
    return random.Random(int(semente[:12], 16))


class SessaoSimulada:
    def __init__(self, versao):
        self.versao = versao
        self.turno = 0

    def enviar(self, texto: str) -> Resposta:
        self.turno += 1
        caso = _CASOS.get(texto)
        rng = _rng(self.versao.id, texto, self.turno)
        if caso is None:  # turno intermediário de um caso de memória
            return Resposta("Entendido, anotei essa informação.", rng.uniform(0.4, 1.5), 900, 15)
        acerta = rng.random() < _PERFIL[self.versao.id].get(caso["categoria"], 0.7)
        texto_resp = caso["gabarito"] if acerta else "Posso ajudar com isso. Poderia dar mais detalhes?"
        lat = rng.uniform(0.6, 1.4) * (1.6 if "pro" in self.versao.id else 1.0)
        return Resposta(texto_resp, lat, 900 + 120 * self.turno, len(texto_resp) // 4)


class JuizSimulado:
    modelo = "juiz-simulado"

    def avaliar(self, caso: dict, resposta: str, dataset: dict) -> dict:
        acertou = resposta == caso["gabarito"]
        nota = 5 if acertou else 2
        return {
            "correcao": nota,
            "aderencia_escopo": 5 if acertou else 4,
            "fidelidade": 5 if acertou else 4,
            "comportamento_correto": acertou,
            "recusou": False,
            "justificativa": "Avaliação simulada (sem LLM).",
        }
