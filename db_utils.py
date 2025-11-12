import streamlit as st
import gspread
import pandas as pd
from gspread_dataframe import set_with_dataframe
from datetime import date

# --- CONFIGURAÇÃO DA CONEXÃO ---

# O nome da sua planilha no Google Sheets
SHEET_NAME = "Minhas Finanças Pessoais"
# O nome da "aba" (worksheet) dentro da planilha
TAB_NAME = "Transacoes"

@st.cache_resource(ttl=600) # Cacheia a conexão por 10 minutos
def get_google_sheet_connection():
    """
    Conecta ao Google Sheets usando as credenciais armazenadas
    nos "Secrets" do Streamlit.
    """
    try:
        creds_json = st.secrets["google_sheets_credentials"]
        gc = gspread.service_account_from_dict(creds_json)
    except Exception as e:
        st.error("Erro ao autenticar com o Google Sheets.")
        st.error(f"Verifique seus Streamlit Secrets. Erro: {e}")
        return None
    
    try:
        sh = gc.open(SHEET_NAME)
        return sh
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Planilha '{SHEET_NAME}' não encontrada.")
        st.error("Verifique o nome da planilha e se você a compartilhou com o email da conta de serviço.")
        return None
    except Exception as e:
        st.error(f"Erro ao abrir a planilha: {e}")
        return None

@st.cache_resource(ttl=600) # Cacheia a aba por 10 minutos
def get_worksheet():
    """
    Abre a planilha e a aba (worksheet) específica.
    Cria a aba e o cabeçalho se não existirem.
    """
    sh = get_google_sheet_connection()
    if sh is None:
        return None
        
    try:
        ws = sh.worksheet(TAB_NAME)
        return ws
    except gspread.exceptions.WorksheetNotFound:
        st.info(f"Aba '{TAB_NAME}' não encontrada, criando uma nova...")
        ws = sh.add_worksheet(title=TAB_NAME, rows="100", cols="20")
        
        headers = ['data', 'descricao', 'categoria', 'valor', 'cartao']
        ws.append_row(headers)
        st.success(f"Aba '{TAB_NAME}' criada com sucesso.")
        return ws
    except Exception as e:
        st.error(f"Erro ao acessar a aba '{TAB_NAME}': {e}")
        return None

def add_transaction(data, descricao, categoria, valor, cartao):
    """Adiciona uma nova linha (transação) na planilha."""
    ws = get_worksheet()
    if ws is None:
        return False
        
    try:
        nova_linha = [data, descricao, categoria, valor, cartao]
        ws.append_row(nova_linha)
        # Limpa o cache dos dados para forçar a releitura
        get_transactions.clear_cache()
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar transação na planilha: {e}")
        return False

@st.cache_data(ttl=300) # Cacheia os dados por 5 minutos
def get_transactions():
    """Busca todas as transações da planilha e retorna como um DataFrame."""
    ws = get_worksheet()
    if ws is None:
        return pd.DataFrame(columns=['data', 'descricao', 'categoria', 'valor', 'cartao'])
        
    try:
        data = ws.get_all_records()
        
        if not data:
            return pd.DataFrame(columns=['data', 'descricao', 'categoria', 'valor', 'cartao'])
            
        df = pd.DataFrame(data)
        
        expected_cols = ['data', 'descricao', 'categoria', 'valor', 'cartao']
        if df.empty:
             return pd.DataFrame(columns=expected_cols)

        if not all(col in df.columns for col in expected_cols):
            st.error(f"O cabeçalho da planilha está incorreto. Esperado: {expected_cols}. Encontrado: {list(df.columns)}")
            return pd.DataFrame(columns=expected_cols)

        df = df[expected_cols]
        df = df.iloc[::-1].reset_index(drop=True) 
        
        return df
    except Exception as e:
        st.error(f"Erro ao ler dados da planilha: {e}")
        return pd.DataFrame(columns=['data', 'descricao', 'categoria', 'valor', 'cartao'])

def initialize_db():
    """
    Função de inicialização. Apenas verifica a conexão
    e cria a aba se necessário.
    """
    print("Verificando conexão com Google Sheets...")
    ws = get_worksheet()
    if ws:
        print("Conexão com Google Sheets OK.")
    else:
        print("Falha na verificação do Google Sheets.")
