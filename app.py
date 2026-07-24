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
SPREADSHEET_URL = "ここにスプレッドシートのURLを貼り付ける"
workbook = gc.open_by_url(SPREADSHEET_URL)
worksheet = workbook.get_worksheet(0)

# --- 2. Obtenção de Dados ---
data = worksheet.get_all_values()
df = pd.DataFrame(data[1:], columns=data[0])

# --- Inicialização do Session State (状態の初期化) ---
if 'step' not in st.session_state:
    st.session_state.step = 1  
if 'saved_msg' not in st.session_state:
    st.session_state.saved_msg = False

# 【重要】フォームをリセットするためのカウンター
if 'form_counter' not in st.session_state:
    st.session_state.form_counter = 0


# --- UI ---
st.title("🌱 Aplicativo de Coleta de Dados")
st.write("Insira os dados da planta. (Dados de Abril)")

if st.session_state.saved_msg:
    st.success("✅ Dados salvos com sucesso! Pode inserir o próximo dado.")
    st.session_state.saved_msg = False 


# --- 3. Fluxo do Aplicativo ---

# ==========================================
# ステップ1：Line ID と Plant ID の検索画面
# ==========================================
if st.session_state.step == 1:
    
    # keyにカウンターをつけることで、リセット時に全く新しい入力欄として認識させる
    line_number = st.number_input(
        "Número da Linha (ex: '1' para L1)", 
        min_value=1, step=1, format="%d", value=None, placeholder="Ex: 1",
        key=f"line_{st.session_state.form_counter}"
    )
    plant_no = st.number_input(
        "Número da Planta (Plant No)", 
        min_value=1, step=1, format="%d", value=None, placeholder="Ex: 3",
        key=f"plant_{st.session_state.form_counter}"
    )
    
    if st.button("🔍 Buscar (検索)"):
        if line_number is not None and plant_no is not None:
            selected_line = f"L{line_number}"
            plant_no_str = str(int(plant_no))
            
            target_row = df[(df['Line Number'] == selected_line) & 
                            ((df['No of plant'] == plant_no_str) | (df['No of plant'] == f"{plant_no_str}.0"))]
            
            if target_row.empty:
                st.error("⚠️ A combinação de Número da Linha e Número da Planta não existe.")
            else:
                # 次の画面で使う情報を保存
                st.session_state.mother_id = target_row['Mother Id'].values[0]
                st.session_state.row_index = target_row.index[0] + 2
                
                current_val_str = str(target_row.iloc[0, 5])
                if current_val_str.strip() == "" or current_val_str.lower() == "nan" or current_val_str.lower() == "none":
                    st.session_state.current_val = 0
                else:
                    try:
                        st.session_state.current_val = int(float(current_val_str))
                    except ValueError:
                        st.session_state.current_val = 0
                        
                # ステップ2へ
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
        step=1, format="%d", value=None, placeholder="Digite o valor",
        key=f"april_{st.session_state.form_counter}"
    )
    
    # 変更点：カラムの幅の比率を 3:1 (あるいは 4:1) に設定し、左を大きく、右を小さくする
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # use_container_width=True でカラム幅いっぱいに広げ、type="primary" でボタンを目立たせる
        if st.button("💾 Salvar (保存)", use_container_width=True, type="primary"):
            if april_value is None:
                st.warning("⚠️ Por favor, insira o valor medido antes de salvar.")
            else:
                try:
                    new_value = st.session_state.current_val + april_value
                    worksheet.update_cell(st.session_state.row_index, 6, new_value) # F列に保存
                    
                    st.session_state.saved_msg = True
                    
                    # --- 成功したらカウンターを増やして入力欄を初期化 ---
                    st.session_state.form_counter += 1
                    st.session_state.step = 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
                    
    with col2:
        # こちらも use_container_width=True でカラムに合わせる（カラム自体が小さいのでボタンも小さくなる）
        if st.button("❌ Cancelar (キャンセル)", use_container_width=True):
            # --- キャンセル時もカウンターを増やして入力欄を初期化 ---
            st.session_state.form_counter += 1
            st.session_state.step = 1
            st.rerun()
