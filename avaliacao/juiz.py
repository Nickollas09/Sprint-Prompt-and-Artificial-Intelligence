"""LLM as a judge: um modelo Gemini (diferente dos avaliados) dá as notas.

O juiz recebe a conversa, o gabarito, os critérios de aceite e o contexto de
referência do cenário, e devolve um JSON estruturado. temperature=0 deixa a
avaliação o mais estável possível entre rodadas.
"""
import json
import re
import time

from . import config

PROMPT_JUIZ = """Você é um avaliador rigoroso e imparcial de um chatbot de atendimento.
O chatbot é o "GoodWe ChargeOps Assistant", que atende moradores e síndicos sobre
eletropostos (carregadores de veículos elétricos) em condomínios.

CONTEXTO DE REFERÊNCIA (fatos oficiais do cenário):
{contexto}

CASO DE TESTE {id} — categoria: {categoria} — persona: {persona}
Comportamento esperado: {tipo_esperado} — {definicao_tipo}

CONVERSA (mensagens do usuário, na ordem; a ÚLTIMA resposta do chatbot é a avaliada):
{conversa}

GABARITO (resposta esperada / critério de aceite):
{gabarito}

CRITÉRIOS DE ACEITE:
{criterios}

RESPOSTA DO CHATBOT A AVALIAR (resposta ao último turno):
\"\"\"{resposta}\"\"\"

Avalie e devolva SOMENTE um JSON com estes campos:
- "correcao": inteiro 0–5. Quanto a resposta atende ao gabarito e aos critérios
  (5 = atende todos; 3 = atende o essencial com falhas menores; 0 = errada ou não atende).
  Não penalize diferenças de redação; avalie o conteúdo.
- "aderencia_escopo": inteiro 0–5. Quanto a resposta se mantém no escopo GoodWe/eletropostos
  e no papel de assistente (5 = totalmente; 0 = saiu do papel ou respondeu assunto proibido).
- "fidelidade": inteiro 0–5. Ausência de informação inventada: especificações, preços,
  dados de consumo, regras ou fatos que NÃO estão no contexto de referência nem no gabarito
  (5 = nada inventado; 0 = inventou dados importantes). Pedir esclarecimento ou dizer que
  não tem a informação NÃO é penalizado.
- "comportamento_correto": true/false. A resposta seguiu o comportamento esperado
  ({tipo_esperado})?
- "recusou": true/false. O chatbot se recusou a responder o pedido principal?
- "justificativa": uma ou duas frases curtas explicando as notas.
"""

SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "correcao": {"type": "INTEGER"},
        "aderencia_escopo": {"type": "INTEGER"},
        "fidelidade": {"type": "INTEGER"},
        "comportamento_correto": {"type": "BOOLEAN"},
        "recusou": {"type": "BOOLEAN"},
        "justificativa": {"type": "STRING"},
    },
    "required": ["correcao", "aderencia_escopo", "fidelidade",
                 "comportamento_correto", "recusou", "justificativa"],
}


def montar_prompt(caso: dict, resposta: str, dataset: dict) -> str:
    conversa = "\n".join(f"{i + 1}. Usuário: {t}" for i, t in enumerate(caso["turnos"]))
    return PROMPT_JUIZ.format(
        contexto=dataset["contexto_referencia"],
        id=caso["id"],
        categoria=caso["categoria"],
        persona=caso["persona"],
        tipo_esperado=caso["tipo_esperado"],
        definicao_tipo=dataset["tipos_esperados"][caso["tipo_esperado"]],
        conversa=conversa,
        gabarito=caso["gabarito"],
        criterios="\n".join(f"- {c}" for c in caso["criterios"]),
        resposta=resposta,
    )


def _validar(dados: dict) -> dict:
    for campo in ("correcao", "aderencia_escopo", "fidelidade"):
        dados[campo] = max(0, min(5, int(dados[campo])))
    dados["comportamento_correto"] = bool(dados["comportamento_correto"])
    dados["recusou"] = bool(dados["recusou"])
    return dados


def _extrair_json(texto: str) -> dict:
    m = re.search(r"\{.*\}", texto, re.S)
    if not m:
        raise ValueError(f"juiz não devolveu JSON: {texto[:200]}")
    return json.loads(m.group(0))


class Juiz:
    def __init__(self, modelo: str = config.MODELO_JUIZ):
        from google import genai
        from google.genai import types

        self.modelo = modelo
        self._types = types
        self.client = genai.Client(api_key=config.chave_api())

    def avaliar(self, caso: dict, resposta: str, dataset: dict, tentativas: int = 4) -> dict:
        types = self._types
        cfg = types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_schema=SCHEMA,
        )
        prompt = montar_prompt(caso, resposta, dataset)
        ultimo_erro = None
        for n in range(tentativas):
            try:
                resp = self.client.models.generate_content(
                    model=self.modelo, contents=prompt, config=cfg
                )
                return _validar(_extrair_json(resp.text or ""))
            except Exception as e:  # rede, cota (429) ou JSON inválido
                ultimo_erro = e
                time.sleep(5 * (3 ** n))
        return {"erro": f"{type(ultimo_erro).__name__}: {ultimo_erro}"}
