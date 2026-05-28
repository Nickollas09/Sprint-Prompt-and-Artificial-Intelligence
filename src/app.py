import streamlit as st
from bot_logic import configurar_chat_com_memoria

st.set_page_config(page_title="GoodWe ChargeOps Assistant", page_icon="⚡", layout="centered")

st.title("⚡ GoodWe ChargeOps Assistant")
st.caption(" Solução inteligente para gestão de eletropostos condominiais — EV Challenge 2026")
st.divider()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Como posso ajudar com a recarga do seu VE hoje?"):

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        chat_sessao = configurar_chat_com_memoria(st.session_state.messages[:-1])

        resposta_ia = chat_sessao.send_message(prompt)
        texto_resposta = resposta_ia.text

        with st.chat_message("assistant"):
            st.markdown(texto_resposta)

        st.session_state.messages.append({"role": "assistant", "content": texto_resposta})
        
    except Exception as e:
        st.error(f"Ocorreu um erro de comunicação com a Inteligência Artificial: {e}")