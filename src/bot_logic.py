import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

load_dotenv()

store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    """Recupera ou cria o histórico de mensagens gerenciado nativamente pelo LangChain."""
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

def carregar_system_prompt() -> str:
    caminho_prompt = os.path.join(os.path.dirname(__file__), '..', 'config', 'system_prompt.txt')
    try:
        with open(caminho_prompt, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Você é o assistente GoodWe. Responda cordialmente no escopo de eletropostos."

def criar_agente_goodwe(model_name: str = "gemini-1.5-flash", temperature: float = 0.7, top_p: float = 0.95):
    """
    Cria uma cadeia LangChain estruturada com controle de modelo, 
    parâmetros customizados e suporte nativo à memória conversacional.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("ERRO: Variable GEMINI_API_KEY não foi encontrada no .env")

    llm = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature,
        top_p=top_p,
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", carregar_system_prompt()),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    chain = prompt_template | llm

    agent_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    return agent_with_history