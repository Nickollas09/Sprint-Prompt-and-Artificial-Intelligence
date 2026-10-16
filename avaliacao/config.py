"""Configurações do pipeline de avaliação (Sprint 04).

Todos os nomes de modelo podem ser trocados pelo .env, sem mexer no código.
Nenhuma chave de API fica no código: ela é lida de GEMINI_API_KEY.
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv ausente: usa só as variáveis de ambiente
    def load_dotenv(*_a, **_k):
        return False

RAIZ = Path(__file__).resolve().parent.parent
PASTA_AVALIACAO = RAIZ / "avaliacao"
PASTA_RESULTADOS = RAIZ / "resultados"
DATASET = PASTA_AVALIACAO / "golden_dataset.json"
AVALIACAO_MANUAL = PASTA_AVALIACAO / "avaliacao_manual_sprint3.json"
EQUIPE = PASTA_AVALIACAO / "equipe.json"

PROMPT_SPRINT2 = PASTA_AVALIACAO / "versoes" / "system_prompt_sprint2.txt"
PROMPT_SPRINT3 = RAIZ / "config" / "system_prompt.txt"

load_dotenv(RAIZ / ".env")

# Modelos dos agentes avaliados.
# O gemini-1.5-flash (usado na Sprint 2) foi desligado pelo Google em set/2025,
# então a versão Sprint 2 roda com o mesmo modelo da Sprint 3 por padrão.
# Assim a comparação isola a ARQUITETURA + PROMPT, e não o modelo.
MODELO_SPRINT2 = os.getenv("MODELO_SPRINT2", "gemini-2.5-flash")
MODELO_FLASH = os.getenv("MODELO_FLASH", "gemini-2.5-flash")
MODELO_PRO = os.getenv("MODELO_PRO", "gemini-2.5-pro")

# Modelo juiz: de propósito DIFERENTE dos modelos avaliados,
# para reduzir o viés de um modelo "dar nota alta para si mesmo".
MODELO_JUIZ = os.getenv("MODELO_JUIZ", "gemini-3.8-flash")


def chave_api() -> str:
    chave = os.getenv("GEMINI_API_KEY")
    if not chave:
        raise SystemExit(
            "GEMINI_API_KEY não encontrada. Crie o arquivo .env na raiz do projeto "
            "(veja .env.example) ou rode com --simulado para testar sem API."
        )
    return chave
