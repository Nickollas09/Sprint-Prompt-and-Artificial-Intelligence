import os

def gerar_resposta_chatbot(mensagem_usuario: str) -> str:
    """
    Função principal que fará a chamada para a API do Google Gemini
    utilizando as diretrizes do system_prompt.txt.
    (Implementação completa na Sprint 2)
    """
    
    if not mensagem_usuario:
        return "Olá! Como posso ajudar você no EV ChargeOps hoje?"
        
    return f"[Mock] Recebi sua mensagem: '{mensagem_usuario}'. A integração com o Gemini será finalizada na Sprint 2."