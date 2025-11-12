import streamlit as st
import pandas as pd
import db_utils as db
from datetime import date
import plotly.express as px

# Configuração da página
st.set_page_config(
    page_title="Meu Controle Financeiro",
    page_icon="💳",
    layout="wide"
)

# --- INICIALIZAÇÃO ---
# Garante que a tabela do banco de dados exista (agora, verifica o Google Sheets)
db.initialize_db()

# --- TÍTULO E CABEÇALHO ---
st.title("Meu Controle de Finanças Pessoais 💸")
st.markdown("Adicione e gerencie seus gastos, com foco especial nos cartões de crédito.")

# --- ABAS (TABS) ---
tab1, tab2, tab3 = st.tabs([" Lançar Gasto ", " Visão Geral ", " Análise por Cartão "])

# --- ABA 1: LANÇAR GASTO ---
with tab1:
    st.header("Insira um novo gasto")
    
    # Criamos um formulário para agrupar os inputs
    with st.form("new_transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            data = st.date_input("Data", date.today())
            descricao = st.text_input("Descrição", placeholder="Ex: Café na padaria")
            categoria = st.selectbox("Categoria", 
                                     ["Alimentação", "Transporte", "Moradia", "Lazer", "Saúde", "Outros"])
        
        with col2:
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            cartao = st.selectbox("Cartão de Crédito",
                                  ["Nenhum (Débito/Dinheiro)", "Nubank", "Inter", "Bradesco", "Itaú", "Outro"])
        
        # Botão de envio do formulário
        submitted = st.form_submit_button("Adicionar Gasto")
        
    if submitted:
        # Validação simples
        if not descricao or valor <= 0:
            st.error("Por favor, preencha a descrição e um valor válido.")
        else:
            # Adiciona ao banco de dados (agora, o Google Sheets)
            if db.add_transaction(data.strftime("%Y-%m-%d"), descricao, categoria, valor, cartao):
                st.success(f"Gasto '{descricao}' de R$ {valor:.2f} adicionado com sucesso!")
            else:
                st.error("Ocorreu um erro ao adicionar o gasto.")

# --- ABA 2: VISÃO GERAL ---
with tab2:
    st.header("Visão Geral dos Seus Gastos")
    
    # Carrega os dados do banco (agora, do Google Sheets)
    df_transactions = db.get_transactions()
    
    if df_transactions.empty:
        st.info("Nenhum gasto registrado ainda. Adicione um na aba 'Lançar Gasto'.")
    else:
        # Converte colunas para os tipos corretos
        try:
            df_transactions['data'] = pd.to_datetime(df_transactions['data'])
            df_transactions['valor'] = pd.to_numeric(df_transactions['valor'])
        except Exception as e:
            st.error(f"Erro ao processar os dados da planilha. Verifique se há valores estranhos. Erro: {e}")
            # Mostra o dataframe 'cru' para debugging
            st.dataframe(df_transactions)
            st.stop()

        # Métricas principais
        total_gasto = df_transactions['valor'].sum()
        gasto_medio = df_transactions['valor'].mean()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Gasto", f"R$ {total_gasto:.2f}")
        col2.metric("Gasto Médio por Transação", f"R$ {gasto_medio:.2f}")
        
        st.markdown("---")
        
        # Gráfico de gastos por categoria (usando Plotly)
        st.subheader("Gastos por Categoria")
        df_categoria = df_transactions.groupby('categoria')['valor'].sum().reset_index()
        fig_cat = px.bar(df_categoria, 
                         x='categoria', 
                         y='valor', 
                         title="Total gasto por categoria",
                         labels={'valor': 'Total Gasto (R$)', 'categoria': 'Categoria'},
                         template="plotly_white")
        st.plotly_chart(fig_cat, use_container_width=True)

        # Tabela de transações recentes
        st.subheader("Histórico de Transações")
        st.dataframe(df_transactions.sort_values(by='data', ascending=False), use_container_width=True)

# --- ABA 3: ANÁLISE POR CARTÃO ---
with tab3:
    st.header("Análise Específica do Cartão de Crédito")
    st.markdown("Filtre seus gastos para ver o impacto de cada cartão.")

    df_transactions_card = db.get_transactions()
    
    if df_transactions_card.empty:
        st.info("Nenhum gasto registrado ainda.")
    else:
        # Tenta converter o valor para numérico
        try:
            df_transactions_card['valor'] = pd.to_numeric(df_transactions_card['valor'])
        except Exception as e:
            st.error(f"Erro ao processar dados de valor: {e}")
            st.stop() # Para a execução da aba se os dados não forem válidos

        # Filtra apenas transações que não sejam "Nenhum"
        df_cartoes = df_transactions_card[df_transactions_card['cartao'] != "Nenhum (Débito/Dinheiro)"]
        
        if df_cartoes.empty:
            st.info("Nenhum gasto no cartão de crédito registrado.")
        else:
            
            # Filtro de seleção de cartão
            lista_cartoes = df_cartoes['cartao'].unique()
            cartao_selecionado = st.selectbox("Selecione um Cartão", lista_cartoes)
            
            # Filtra o dataframe pelo cartão selecionado
            df_filtrado = df_cartoes[df_cartoes['cartao'] == cartao_selecionado]
            
            if df_filtrado.empty:
                st.warning(f"Nenhum gasto encontrado para o cartão '{cartao_selecionado}'.")
            else:
                total_gasto_cartao = df_filtrado['valor'].sum()
                num_transacoes_cartao = len(df_filtrado)
                
                st.subheader(f"Resumo do Cartão: {cartao_selecionado}")
                col1, col2 = st.columns(2)
                col1.metric("Total Gasto no Cartão", f"R$ {total_gasto_cartao:.2f}")
                col2.metric("Número de Transações", num_transacoes_cartao)
                
                # Gráfico de gastos por categoria para o cartão selecionado
                st.markdown("---")
                st.subheader(f"Gastos por Categoria ({cartao_selecionado})")
                df_categoria_cartao = df_filtrado.groupby('categoria')['valor'].sum().reset_index()
                
                fig_cat_cartao = px.pie(df_categoria_cartao, 
                                        names='categoria', 
                                        values='valor',
                                        title=f"Distribuição de gastos para o cartão {cartao_selecionado}",
                                        hole=0.3)
                fig_cat_cartao.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_cat_cartao, use_container_width=True)
                
                # Tabela de transações do cartão
                st.subheader(f"Transações do Cartão: {cartao_selecionado}")
                st.dataframe(df_filtrado.sort_values(by='data', ascending=False), use_container_width=True)
