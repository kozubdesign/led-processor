import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps

# ====================== ФУНКЦИИ ПОИСКА ФАЙЛОВ ======================
def find_file_case_insensitive(filename):
    """Ищет файл в корне, игнорируя регистр (находит logo_H.png если просили logo_h.png)"""
    if os.path.exists(filename):
        return filename
    current_dir = os.listdir('.')
    for f in current_dir:
        if f.lower() == filename.lower():
            return f
    return None

# Очищаем кэш если файлы менялись
@st.cache_resource
def get_cached_logo(path):
    found_path = find_file_case_insensitive(path)
    if found_path:
        try:
            return Image.open(found_path).convert("RGBA")
        except Exception as e:
            st.error(f"Ошибка открытия {found_path}: {e}")
            return None
    return None

# ====================== КОНСТАНТЫ ======================
LOGO_H_PATH = "logo_h.png"
LOGO_V_PATH = "logo_v.png"
SOURCE_FOLDER = "images"

# ====================== НАСТРОЙКА ======================
st.set_page_config(page_title="LED Processor", layout="wide")

st.markdown("""
    <style>
    .block-container { max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }
    [data-testid="stHeader"] { display: none; }
    .main-title { text-align: center; font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    div.stButton, div.stDownloadButton, div.element-container:has(button) {
        display: flex !important; justify-content: center !important; width: 100% !important;
    }
    .stButton > button, .stDownloadButton > button {
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important;
    }
    .res-box { 
        text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-title'>Создать контент для LED-экрана</div>", unsafe_allow_html=True)

preview_placeholder = st.empty()
resolution_placeholder = st.empty()

def process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent):
    try:
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo: return None

        with Image.open(bg_path) as img:
            img = ImageOps.fit(img.convert("RGB"), (tw, th), Image.Resampling.LANCZOS)
            lw, lh = active_logo.size
            max_scale = min(tw / lw, th / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
            img.paste(logo_res, ((tw - new_lw)//2, (th - new_lh)//2), logo_res)
            return img
    except: return None

# Загрузка логотипов
logo_h_img = get_cached_logo(LOGO_H_PATH)
logo_v_img = get_cached_logo(LOGO_V_PATH)

bg_files = [os.path.join(SOURCE_FOLDER, f) for f in os.listdir(SOURCE_FOLDER) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []

st.markdown("---")
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
with c1: w_mm = st.number_input("Ширина (мм)", 0, value=0)
with c2: h_mm = st.number_input("Высота (мм)", 0, value=0)
with c3: pitch = st.number_input("Шаг (мм)", min_value=0.0, value=0.0, step=0.1, format="%g")
with c4: logo_scale = st.slider("Размер лого (%)", 0, 100, 70)

if w_mm > 0 and h_mm > 0 and pitch > 0:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))
    is_hor = tw >= th
    current_logo = logo_h_img if is_hor else logo_v_img
    
    if current_logo and bg_files:
        preview = process_single_image(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale)
        if preview:
            buf = io.BytesIO()
            preview.save(buf, format="JPEG", quality=85)
            img_str = base64.b64encode(buf.getvalue()).decode()
            preview_placeholder.markdown(f'''
                <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                    <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 400px; border-radius: 8px; border: 1px solid #ddd;">
                </div>
            ''', unsafe_allow_html=True)
            resolution_placeholder.markdown(f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)
    
    elif not current_logo:
        target_file = LOGO_H_PATH if is_hor else LOGO_V_PATH
        st.error(f"Критическая ошибка: файл **{target_file}** не обнаружен!")
        # Техническая отладка для тебя:
        st.write("Файлы в директории:", os.listdir('.'))

st.markdown("<br>", unsafe_allow_html=True)
button_placeholder = st.empty()

if w_mm > 0 and h_mm > 0 and pitch > 0:
    if button_placeholder.button("Создать контент"):
        button_placeholder.empty()
        with st.spinner("Создание контента..."):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for f in bg_files:
                    processed = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale)
                    if processed:
                        img_byte_arr = io.BytesIO()
                        processed.save(img_byte_arr, format='JPEG', quality=95)
                        zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
            
            st.download_button(label="📥 Скачать контент", data=zip_buffer.getvalue(),
                             file_name=f"led_{tw}x{th}.zip", mime="application/zip")
