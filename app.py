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
# 毎回最新のデータを読み込む
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

# --- Inicialização do Session State (状態の初期化) ---
# step 1: 検索画面, step 2: データ入力画面
if 'step' not in st.session_state:
    st.session_state.step = 1  
if 'saved_msg' not in st.session_state:
    st.session_state.saved_msg = False

# 入力フォームをクリアするためのキーを初期化
if 'line_key' not in st.session_state:
    st.session_state.line_key = None
if 'plant_key' not in st.session_state:
    st.session_state.plant_key = None
if 'april_key' not in st.session_state:
    st.session_state.april_key = None


# --- UI ---
st.title("🌱 Aplicativo de Coleta de Dados")
st.write("Insira os dados da planta. (Dados de Abril)")

# 保存完了メッセージの表示
if st.session_state.saved_msg:
    st.success("✅ Dados salvos com sucesso! Pode inserir o próximo dado.")
    st.session_state.saved_msg = False 


# --- 3. Fluxo do Aplicativo (アプリの画面遷移) ---

# ==========================================
# ステップ1：Line ID と Plant ID の検索画面
# ==========================================
if st.session_state.step == 1:
    
    # widgetにkeyを指定することで、st.session_stateと連動します
    line_number = st.number_input(
        "Número da Linha (ex: '1' para L1)", 
        min_value=1, step=1, format="%d", value=st.session_state.line_key, placeholder="Ex: 1",
        key="line_key"
    )
    plant_no = st.number_input(
        "Número da Planta (Plant No)", 
        min_value=1, step=1, format="%d", value=st.session_state.plant_key, placeholder="Ex: 3",
        key="plant_key"
    )
    
    # 検索ボタンを押すことで次に進む（枠外タップが不要になります）
    if st.button("🔍 Buscar (検索)"):
        if st.session_state.line_key is not None and st.session_state.plant_key is not None:
            selected_line = f"L{st.session_state.line_key}"
            plant_no_str = str(int(st.session_state.plant_key))
            
            target_row = df[(df['Line Number'] == selected_line) & 
                            ((df['No of plant'] == plant_no_str) | (df['No of plant'] == f"{plant_no_str}.0"))]
            
            if target_row.empty:
                st.error("⚠️ A combinação de Número da Linha e Número da Planta não existe.")
            else:
                # 検索成功時：必要な情報をSession Stateに保存し、ステップ2へ進む
                st.session_state.mother_id = target_row['Mother Id'].values[0]
                st.session_state.row_index = target_row.index[0] + 2
                
                # 既存データの確認 (F列: インデックス5)
                current_val_str = str(target_row.iloc[0, 5])
                
                if current_val_str.strip() == "" or current_val_str.lower() == "nan" or current_val_str.lower() == "none":
                    st.session_state.current_val = 0
                else:
                    try:
                        st.session_state.current_val = int(float(current_val_str))
                    except ValueError:
                        st.session_state.current_val = 0
                        
                # 画面をステップ2に切り替える
                st.session_state.step = 2
                st.rerun()
        else:
            st.warning("⚠️ Por favor, insira ambos os números.")

# ==========================================
# ステップ2：Mother ID の確認と測定値の入力・保存
# ==========================================
elif st.session_state.step == 2:
    
    st.success(f"✅ Confirmação: O Mother ID é 【 {st.session_state.mother_id} 】")
    
    if st.session_state.current_val != 0:
        st.info(f"ℹ️ Aviso: Já existe um valor registrado ({st.session_state.current_val}) para esta planta. O novo valor inserido será adicionado a este.")
    
    april_value = st.number_input(
        "Valor medido (Apenas números inteiros)", 
        step=1, format="%d", value=st.session_state.april_key, placeholder="Digite o valor",
        key="april_key"
    )
    
    # ボタンを横並びに配置
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("💾 Salvar (保存)"):
            if st.session_state.april_key is None:
                st.warning("⚠️ Por favor, insira o valor medido antes de salvar.")
            else:
                try:
                    # 計算と保存
                    new_value = st.session_state.current_val + st.session_state.april_key
                    col_index = 6 # F列
                    worksheet.update_cell(st.session_state.row_index, col_index, new_value)
                    
                    # 成功メッセージのフラグを立てる
                    st.session_state.saved_msg = True
                    
                    # --- 【重要】入力値をリセットしてステップ1に戻る ---
                    st.session_state.line_key = None
                    st.session_state.plant_key = None
                    st.session_state.april_key = None
                    st.session_state.step = 1
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
                    
    with col2:
        if st.button("❌ Cancelar (キャンセル)"):
            # キャンセル時も入力値をリセットして戻る
            st.session_state.line_key = None
            st.session_state.plant_key = None
            st.session_state.april_key = None
            st.session_state.step = 1
            st.rerun()
