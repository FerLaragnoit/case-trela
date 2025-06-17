#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Streamlit para o assistente de recomendação de refeições
"""

import streamlit as st
import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.agent_executor import MealRecommendationAgent

st.set_page_config(
    page_title="Assistente de Refeições",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def initialize_agent():
    """Inicializa o agente e mantém em cache"""
    try:
        return MealRecommendationAgent()
    except Exception as e:
        st.warning(f"API da OpenAI não disponível: {e}")
        

def main():
    """Interface principal do Streamlit"""
    
    st.title("Assistente de Recomendação de Refeições")
    st.markdown("""
    Olá! Sou seu assistente para recomendação de refeições movido por **GPT-4o** com **Responses API**.  
    Diga-me o que você está procurando e eu te ajudo a encontrar o prato perfeito! 
    
    """)
    
    agent = initialize_agent()
    if agent:
        st.success("Responses API ativa")
    else:
        st.info("Modo demonstração - Sem API da OpenAI")
    
    with st.sidebar:
        st.header("Exemplos de perguntas")
        st.markdown("""
        - "Quero um prato apimentado com proteína"
        - "Prato sem lactose de até R$ 55"
        - "Refeição saudável com arroz e legumes"
        - "Pratos veganos de até R$ 40"
        - "Quero o prato mais barato"
        - "Almoço prático, sou intolerante a lactose"
        """)
        
        st.divider()
        
        
        st.header("Configurações")
        if st.button("Reiniciar conversa"):
            st.session_state.messages = []
            st.rerun()
    agent = initialize_agent()
    
    if agent is None:
        st.error("Não foi possível inicializar o agente. Verifique sua API key da OpenAI.")
        st.info("Configure sua API key no arquivo `.env`")
        return
    
    is_offline = hasattr(agent, '__class__') and agent.__class__.__name__ == 'OfflineMealAgent'
    if is_offline:
        st.info("**Modo Demonstração:** Simulando comportamento do agente (sem API da OpenAI)")
    else:
        st.success("**Modo Online:** Conectado à API da OpenAI")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "Olá! Como posso ajudá-lo a encontrar uma refeição hoje?"
            }
        ]
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Digite sua solicitação aqui..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("Analisando sua solicitação..."):
                try:
                    response = agent.chat(prompt)
                    
                    st.markdown(response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    error_msg = f"Ocorreu um erro: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

def demo_page():
    """Página com casos de demonstração"""
    
    st.title("Demonstração")
    st.markdown("Teste o assistente com casos pré-definidos dos requisitos:")
    
    demo_cases = [
        "Quero um prato apimentado, que tenha proteína",
        "Prato sem lactose de até R$55", 
        "Refeição saudável com proteína, arroz e legumes",
        "Pratos veganos de até R$40",
        "Quero um almoço prático, sou intolerante a lactose",
        "Quero o prato mais barato"
    ]

    agent = initialize_agent()
    
    if agent is None:
        st.error("Não foi possível inicializar o agente.")
        return
    
    is_offline = hasattr(agent, '__class__') and agent.__class__.__name__ == 'OfflineMealAgent'
    if is_offline:
        st.info("**Modo Demonstração:** Simulando comportamento do agente")

    for i, case in enumerate(demo_cases, 1):
        st.subheader(f"Caso {i}")
        
        with st.expander(f"**{case}**", expanded=False):
            if st.button(f"Testar caso {i}", key=f"demo_{i}"):
                with st.spinner("Processando..."):
                    try:
                        response = agent.get_recommendation(case)
                        st.success("**Resposta:**")
                        st.markdown(response)
                    except Exception as e:
                        st.error(f"Erro: {e}")

def main_app():
    """Aplicação principal com navegação"""
    
    with st.sidebar:
        st.title("Navegação")
        page = st.radio(
            "Escolha uma página:",
            ["Chat", "Demonstração"],
            index=0
        )
    
    if page == "Chat":
        main()
    elif page == "Demonstração":
        demo_page()

if __name__ == "__main__":
    main_app()
