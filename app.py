import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Configuração da Página ---
st.set_page_config(page_title="Aplicativo de Coleta de Dados", page_icon="🌱")

# --- 1. Configuração de Conexão ---
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

try:
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
except FileNotFoundError:
    credentials = Credentials.from_service_account_file(
        "credentials.json", scopes=scopes
    )

gc = gspread.authorize(credentials)

# ※ご自身のスプレッドシートURLを設定してください
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1JMHE0MGolPnkFlYu04om-AiXzJxqFWW1Cd7IwRKpJmM/edit?gid=864123872#gid=864123872"
workbook = gc.open_by_url(SPREADSHEET_URL)
worksheet = workbook.get_worksheet(0)

# --- 2. Obtenção de Dados ---
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

# --- UI ---
st.title("🌱 Aplicativo de Coleta de Dados")
st.write("Insira os dados da planta. (Dados de Abril)")

if 'saved_msg' not in st.session_state:
    st.session_state.saved_msg = False

if st.session_state.saved_msg:
    st.success("✅ Dados salvos com sucesso! Pode inserir o próximo dado.")
    st.session_state.saved_msg = False 

# --- 3. Formulário de Busca (検索フォーム) ---
# フォームにすることで、スマホのエンターキーでスムーズに動作します
with st.form("search_form"):
    st.write("🔍 1. Buscar Planta")
    line_number_input = st.number_input(
        "Número da Linha (ex: '1' para L1)", 
        min_value=1, step=1, format="%d", value=None, placeholder="Ex: 1",
        key="line_key"
    )
    plant_no = st.number_input(
        "Número da Planta (Plant No)", 
        min_value=1, step=1, format="%d", value=None, placeholder="Ex: 3",
        key="plant_key"
    )
    # エンターを押すと、このボタンが自動的に押されたことになります
    searched = st.form_submit_button("Buscar (エンター)")

st.divider()

# --- 4. Confirmação e Entrada de Dados (データ入力) ---
# Line NoとPlant Noの両方が入力されている場合のみ次を表示
if st.session_state.line_key is not None and st.session_state.plant_key is not None:
    selected_line = f"L{st.session_state.line_key}"
    plant_no_str = str(int(st.session_state.plant_key))
    
    target_row = df[(df['Line Number'] == selected_line) & 
                    ((df['No of plant'] == plant_no_str) | (df['No of plant'] == f"{st.session_state.plant_key}.0"))]

    if target_row.empty:
        st.error("⚠️ A combinação de Número da Linha e Número da Planta não existe.")
    else:
        mother_id = target_row['Mother Id'].values[0]
        st.success(f"✅ Confirmação: O Mother ID é 【 {mother_id} 】")
        
        # 既存データの確認
        current_val_str = str(target_row.iloc[0, 5]) 
        
        if current_val_str.strip() == "" or current_val_str.lower() == "nan" or current_val_str.lower() == "none":
            current_val = 0
        else:
            try:
                current_val = int(float(current_val_str))
            except ValueError:
                current_val = 0
        
        if current_val != 0:
            st.info(f"ℹ️ Aviso: Já existe um valor registrado ({current_val}) para esta planta. O novo valor inserido será adicionado a este.")
        
        st.write("📝 2. Inserir Dados")
        april_value = st.number_input(
            "Valor medido (Apenas números inteiros)", 
            step=1, format="%d", value=None, placeholder="Digite o valor",
            key="april_key"
        )
        
        if st.button("Salvar na Planilha"):
            if april_value is None:
                st.warning("⚠️ Por favor, insira o valor medido antes de salvar.")
            else:
                row_index = target_row.index[0] + 2 
                col_index = 6 # F列
                
                try:
                    # 計算と保存
                    new_value = current_val + april_value
                    worksheet.update_cell(row_index, col_index, new_value)
                    
                    st.session_state.saved_msg = True
                    
                    # 【重要】単なる消去ではなく、明示的に None（空）を代入して確実に入力欄をリセットする
                    st.session_state.line_key = None
                    st.session_state.plant_key = None
                    st.session_state.april_key = None
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
else:
    st.info("ℹ️ Por favor, insira o Número da Linha e o Número da Planta e clique em 'Buscar'.")
