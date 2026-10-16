"""Adaptadores das versões do agente que o pipeline avalia.

Cada versão expõe a mesma interface: `nova_sessao()` devolve um objeto com
`enviar(texto) -> Resposta`. Assim o pipeline trata todas as versões igual,
e uma sessão nova por caso de teste garante que um caso não "vaze" memória
para o outro.

Versões:
  sprint2_manual  -> reprodução fiel do bot_logic.py da Sprint 2 (commit 1f2fdc3):
                     SDK google-genai chamado direto, histórico montado à mão,
                     system prompt da Sprint 1/2.
  sprint3_flash   -> código atual (src/bot_logic.py): LangChain +
                     RunnableWithMessageHistory, prompt com guardrails, Flash.
  sprint3_pro     -> mesma arquitetura da Sprint 3 com o modelo Pro.
"""
import sys
import time
import uuid
from dataclasses import dataclass, field

from . import config


@dataclass
class Resposta:
    texto: str
    latencia_s: float
    tokens_entrada: int | None = None
    tokens_saida: int | None = None
    erro: str | None = None


@dataclass
class Versao:
    id: str
    nome: str
    descricao: str
    arquitetura: str
    modelo: str
    prompt_path: str
    parametros: dict = field(default_factory=dict)

    def system_prompt(self) -> str:
        with open(self.prompt_path, encoding="utf-8") as f:
            return f.read()


VERSOES = {
    "sprint2_manual": Versao(
        id="sprint2_manual",
        nome="Sprint 2 (manual)",
        descricao="Chamada direta ao SDK google-genai, histórico manual, prompt da Sprint 1/2",
        arquitetura="SDK google-genai direto",
        modelo=config.MODELO_SPRINT2,
        prompt_path=str(config.PROMPT_SPRINT2),
        parametros={"temperature": 0.7},
    ),
    "sprint3_flash": Versao(
        id="sprint3_flash",
        nome="Sprint 3 (LangChain + Flash)",
        descricao="LangChain RunnableWithMessageHistory, prompt com guardrails, modelo Flash",
        arquitetura="LangChain (RunnableWithMessageHistory)",
        modelo=config.MODELO_FLASH,
        prompt_path=str(config.PROMPT_SPRINT3),
        parametros={"temperature": 0.7, "top_p": 0.95},
    ),
    "sprint3_pro": Versao(
        id="sprint3_pro",
        nome="Sprint 3 (LangChain + Pro)",
        descricao="Mesma arquitetura da Sprint 3 com o modelo Pro",
        arquitetura="LangChain (RunnableWithMessageHistory)",
        modelo=config.MODELO_PRO,
        prompt_path=str(config.PROMPT_SPRINT3),
        parametros={"temperature": 0.7, "top_p": 0.95},
    ),
}


def _texto_de(conteudo) -> str:
    """Modelos Gemini mais novos podem devolver o conteúdo como lista de partes."""
    if isinstance(conteudo, str):
        return conteudo
    if isinstance(conteudo, list):
        partes = []
        for p in conteudo:
            if isinstance(p, str):
                partes.append(p)
            elif isinstance(p, dict) and p.get("type") == "text":
                partes.append(p.get("text", ""))
        return "".join(partes)
    return str(conteudo)


# ---------------------------------------------------------------- Sprint 2 --
class SessaoSprint2:
    """Reproduz a lógica de configurar_chat_com_memoria() da Sprint 2."""

    def __init__(self, versao: Versao):
        from google import genai
        from google.genai import types

        self._types = types
        self.versao = versao
        self.client = genai.Client(api_key=config.chave_api())
        self.prompt = versao.system_prompt()
        self.historico = []  # memória manual, como o st.session_state da Sprint 2

    def enviar(self, texto: str) -> Resposta:
        types = self._types
        cfg = types.GenerateContentConfig(
            system_instruction=self.prompt,
            temperature=self.versao.parametros["temperature"],
        )
        chat = self.client.chats.create(
            model=self.versao.modelo, history=list(self.historico), config=cfg
        )
        inicio = time.perf_counter()
        resp = chat.send_message(texto)
        latencia = time.perf_counter() - inicio
        saida = resp.text or ""
        self.historico.append(types.Content(role="user", parts=[types.Part.from_text(text=texto)]))
        self.historico.append(types.Content(role="model", parts=[types.Part.from_text(text=saida)]))
        uso = resp.usage_metadata
        return Resposta(
            texto=saida,
            latencia_s=latencia,
            tokens_entrada=getattr(uso, "prompt_token_count", None),
            tokens_saida=getattr(uso, "candidates_token_count", None),
        )


# ---------------------------------------------------------------- Sprint 3 --
class SessaoSprint3:
    """Usa o próprio src/bot_logic.py da Sprint 3, sem alterações."""

    def __init__(self, versao: Versao):
        pasta_src = str(config.RAIZ / "src")
        if pasta_src not in sys.path:
            sys.path.insert(0, pasta_src)
        import bot_logic  # noqa: E402  (módulo da Sprint 3)

        config.chave_api()  # falha cedo se a chave não existir
        self.versao = versao
        self.agente = bot_logic.criar_agente_goodwe(
            model_name=versao.modelo,
            temperature=versao.parametros["temperature"],
            top_p=versao.parametros["top_p"],
        )
        # session_id único: memória isolada por caso de teste
        self.session_id = f"eval-{versao.id}-{uuid.uuid4().hex[:8]}"

    def enviar(self, texto: str) -> Resposta:
        inicio = time.perf_counter()
        resp = self.agente.invoke(
            {"input": texto}, config={"configurable": {"session_id": self.session_id}}
        )
        latencia = time.perf_counter() - inicio
        uso = getattr(resp, "usage_metadata", None) or {}
        return Resposta(
            texto=_texto_de(resp.content),
            latencia_s=latencia,
            tokens_entrada=uso.get("input_tokens"),
            tokens_saida=uso.get("output_tokens"),
        )


def nova_sessao(versao_id: str, simulado: bool = False):
    versao = VERSOES[versao_id]
    if simulado:
        from .simulado import SessaoSimulada

        return SessaoSimulada(versao)
    if versao_id.startswith("sprint2"):
        return SessaoSprint2(versao)
    return SessaoSprint3(versao)
