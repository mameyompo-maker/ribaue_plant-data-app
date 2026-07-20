import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- ページ設定 (タブのタイトルなどをポルトガル語に) ---
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

# セッションステート（状態管理）の初期化
if 'saved' not in st.session_state:
    st.session_state.saved = False

# --- 3. Formulário de Busca e Entrada (検索と入力フォーム) ---
# "L" を省略し、数値のみ入力させる
line_number_input = st.number_input("Número da Linha (ex: digite '1' para L1)", min_value=1, step=1, format="%d")
# プログラム内部で "L" を結合して検索用に整形
selected_line = f"L{line_number_input}"

plant_no = st.number_input("Número da Planta (Plant No)", min_value=1, step=1, format="%d")
plant_no_str = str(int(plant_no))

target_row = df[(df['Line Number'] == selected_line) & 
                ((df['No of plant'] == plant_no_str) | (df['No of plant'] == f"{plant_no}.0"))]

st.divider()

if target_row.empty:
    st.error("⚠️ A combinação de Número da Linha e Número da Planta não existe.")
else:
    mother_id = target_row['Mother Id'].values[0]
    st.success(f"✅ Confirmação: O Mother ID é 【 {mother_id} 】")
    
    # 計測値を整数 (step=1, format="%d") で入力するように変更
    april_value = st.number_input("Valor medido (Apenas números inteiros)", step=1, format="%d")
    
    # 保存ボタン
    if st.button("Salvar na Planilha"):
        row_index = target_row.index[0] + 2 
        col_index = 6 # F列
        
        try:
            worksheet.update_cell(row_index, col_index, april_value)
            st.session_state.saved = True # 保存完了フラグを立てる
            st.rerun() # 画面をリロードして即座にUIを更新
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

# --- 4. Mensagem de Sucesso e Reset (成功メッセージとリセット) ---
if st.session_state.saved:
    st.info("✅ Dados salvos com sucesso na planilha!")
    # 「次の入力へ」ボタンを表示
    if st.button("Inserir Próximo Dado"):
        st.session_state.saved = False # フラグを戻してリロード
        st.rerun()