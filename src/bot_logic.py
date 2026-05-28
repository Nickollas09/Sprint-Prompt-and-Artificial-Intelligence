import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def carregar_system_prompt() -> str:
    """Lê as diretrizes do robô direto do arquivo de configuração da Sprint 1."""
    caminho_prompt = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_prompt.txt')
    try:
        with open(caminho_prompt, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Você é o EV ChargeOps Assistant para a GoodWe. Responda cordialmente dentro do escopo."

def iniciar_cliente_gemini():
    """Inicializa o cliente oficial da API de forma segura."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("ERRO CRÍTICO: A variável GEMINI_API_KEY não foi configurada no arquivo .env!")
    return genai.Client(api_key=api_key)

def configurar_chat_com_memoria(historico_streamlit):
    """
    Injeta o System Prompt e converte o histórico do Streamlit para 
    o formato aceito pela API do Gemini, mantendo o contexto da conversa.
    """
    client = iniciar_cliente_gemini()
    prompt_sistema = carregar_system_prompt()
    
    historico_gemini = []
    for msg in historico_streamlit:
        role_gemini = "user" if msg["role"] == "user" else "model"
        historico_gemini.append(
            types.Content(
                role=role_gemini,
                parts=[types.Part.from_text(text=msg["content"])]
            )
        )
    
    config = types.GenerateContentConfig(
        system_instruction=prompt_sistema,
        temperature=0.7
    )
    
    chat = client.chats.create(
        model="gemini-1.5-flash",
        history=historico_gemini,
        config=config
    )
    return chat