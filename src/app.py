import streamlit as st
from bot_logic import gerar_resposta_chatbot

st.set_page_config(page_title="GoodWe ChargeOps Assistant", page_icon="⚡")

st.title("⚡ GoodWe ChargeOps Assistant")
st.subheader("Gerenciamento Inteligente de Eletropostos Condominiais")

if "messages" not in st.session_state:
    st.session_state.messages = []

if prompt := st.chat_input("Digite sua dúvida (ex: Regras de agendamento)..."):

    st.chat_message("user").markdown(prompt)

    resposta = gerar_resposta_chatbot(prompt)
    
    st.chat_message("assistant").markdown(resposta)