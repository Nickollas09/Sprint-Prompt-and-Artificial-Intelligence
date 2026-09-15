import streamlit as st
from bot_logic import criar_agente_goodwe, store

st.set_page_config(page_title="GoodWe ChargeOps Agent", layout="wide")

st.title(" GoodWe ChargeOps Agent (Sprint 3)")
st.caption(" Agente Orquestrado com LangChain & Guardrails de Segurança — EV Challenge 2026")
st.divider()

with st.sidebar:
    st.header(" Configurações do Agente")
    st.info("Estrutura Orquestrada via **LangChain Framework**")
    
    modelo_selecionado = st.selectbox(
        "Selecione o Modelo LLM:",
        ["gemini-2.5-flash", "gemini-2.5-pro"]
    )
    
    temp = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.1)
    top_p = st.slider("Top P:", 0.1, 1.0, 0.95, 0.05)
    
    session_id = st.text_input("ID da Sessão (Memória):", value="sessao_demo_1")
    
    if st.button("Limpar Memória da Sessão"):
        if session_id in store:
            del store[session_id]
        st.session_state.messages = []
        st.success("Memória apagada!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Pergunte ao Agente GoodWe sobre eletropostos..."):
    
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        agente = criar_agente_goodwe(model_name=modelo_selecionado, temperature=temp, top_p=top_p)

        with st.spinner("Agente processando resposta via LangChain..."):
            resposta = agente.invoke(
                {"input": prompt},
                config={"configurable": {"session_id": session_id}}
            )
            texto_resposta = resposta.content

        with st.chat_message("assistant"):
            st.markdown(texto_resposta)
        st.session_state.messages.append({"role": "assistant", "content": texto_resposta})

    except Exception as e:
        st.error(f"Erro ao invocar o agente: {e}")