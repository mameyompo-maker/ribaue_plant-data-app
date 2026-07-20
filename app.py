import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- Configuração da Página (ページ設定) ---
st.set_page_config(page_title="Aplicativo de Coleta de Dados", page_icon="🌱")

# --- 1. Configuração de Conexão (接続設定) ---
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

# --- 2. Obtenção de Dados (データの取得) ---
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

# --- UI ---
st.title("🌱 Aplicativo de Coleta de Dados")
st.write("Insira os dados da planta. (Dados de Abril)")

# セッションステートの初期化
if 'saved' not in st.session_state:
    st.session_state.saved = False

# --- 3. Formulário de Busca e Entrada (検索と入力フォーム) ---
# value=None を指定して、初期状態を「空欄」にします
line_number_input = st.number_input("Número da Linha (ex: '1' para L1)", min_value=1, step=1, format="%d", value=None, placeholder="Ex: 1")
plant_no = st.number_input("Número da Planta (Plant No)", min_value=1, step=1, format="%d", value=None, placeholder="Ex: 3")

st.divider()

# Linha と Planta の両方が入力された場合のみ検索と入力フォームを表示
if line_number_input is not None and plant_no is not None:
    selected_line = f"L{line_number_input}"
    plant_no_str = str(int(plant_no))
    
    target_row = df[(df['Line Number'] == selected_line) & 
                    ((df['No of plant'] == plant_no_str) | (df['No of plant'] == f"{plant_no}.0"))]

    if target_row.empty:
        st.error("⚠️ A combinação de Número da Linha e Número da Planta não existe.")
    else:
        mother_id = target_row['Mother Id'].values[0]
        st.success(f"✅ Confirmação: O Mother ID é 【 {mother_id} 】")
        
        # 計測値も初期状態を「空欄」にします
        april_value = st.number_input("Valor medido (Apenas números inteiros)", step=1, format="%d", value=None, placeholder="Digite o valor")
        
        if st.button("Salvar na Planilha"):
            if april_value is None:
                st.warning("⚠️ Por favor, insira o valor medido antes de salvar.")
            else:
                row_index = target_row.index[0] + 2 
                col_index = 6 # F列
                
                try:
                    # 既にスプレッドシートに入力されている値を取得
                    current_val_str = str(target_row.iloc[0, 5])
                    
                    # 空欄や文字が入っていた場合は 0 として扱う
                    if current_val_str.strip() == "" or current_val_str.lower() == "nan" or current_val_str.lower() == "none":
                        current_val = 0
                    else:
                        try:
                            current_val = int(float(current_val_str))
                        except ValueError:
                            current_val = 0
                    
                    # 【重要】元々の値に、今回入力された値を追加（足し算）する
                    new_value = current_val + april_value
                    
                    worksheet.update_cell(row_index, col_index, new_value)
                    st.session_state.saved = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
else:
    st.info("ℹ️ Por favor, insira o Número da Linha e o Número da Planta para começar.")

# --- 4. Mensagem de Sucesso e Reset (成功メッセージとリセット) ---
if st.session_state.saved:
    st.success("✅ Dados salvos e adicionados ao valor existente na planilha com sucesso!")
    if st.button("Inserir Próximo Dado"):
        st.session_state.saved = False
        st.rerun()
