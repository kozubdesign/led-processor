import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# ====================== ФУНКЦИИ ======================
@st.cache_resource
def get_cached_logo(path):
    if os.path.exists(path):
        try: return Image.open(path).convert("RGBA")
        except: return None
    return None

@st.cache_data
def get_base64_img(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        except: return ""
    return ""

@st.cache_data
def get_bg_files(folder):
    if not os.path.exists(folder): return []
    return [os.path.join(folder, f) for f in os.listdir(folder) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

def process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent, fast=False):
    try:
        resample_method = Image.Resampling.BOX if fast else Image.Resampling.LANCZOS
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo: return None
        with Image.open(bg_path) as img:
            img = ImageOps.fit(img.convert("RGB"), (tw, th), resample_method)
            lw, lh = active_logo.size
            max_scale = min(tw / lw, th / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = active_logo.resize((new_lw, new_lh), resample_method)
            img.paste(logo_res, ((tw - new_lw)//2, (th - new_lh)//2), logo_res)
            return img
    except Exception: return None

def process_to_zip(f, logo_h, logo_v, tw, th, scale):
    processed = process_single_image(f, logo_h, logo_v, tw, th, scale)
    if processed:
        buf = io.BytesIO()
        processed.save(buf, format='JPEG', quality=95)
        return os.path.basename(f), buf.getvalue()
    return None

# ====================== НАСТРОЙКА UI ======================
st.set_page_config(page_title="LED Generator", layout="wide", page_icon="favicon.png")

# Инициализация состояния
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")

st.markdown(f"""
    <style>
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    
    /* Скрытие кнопок +/- во всех числовых инпутах */
    input::-webkit-outer-spin-button,
    input::-webkit-inner-spin-button {{ -webkit-appearance: none; margin: 0; }}
    input[type=number] {{ -moz-appearance: textfield; }}
    
    /* Скрытие подсказок "Press Enter" */
    [data-testid="stInputInstructions"] {{ display: none !important; }}
    
    .logo-container {{ display: flex; justify-content: center; margin-top: 20px; margin-bottom: 20px; }}
    .logo-img {{ width: 150px; }}
    @media (prefers-color-scheme: light) {{ .logo-dark {{ display: none; }} .logo-light {{ display: block; }} }}
    @media (prefers-color-scheme: dark) {{ .logo-light {{ display: none; }} .logo-dark {{ display: block; }} }}
    
    .main-title {{ text-align: center; font-size: 1.6rem; font-weight: bold; margin-bottom: 20px; }}
    
    .stButton > button, .stDownloadButton > button {{
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important;
        border: none !important;
    }}
    .res-box {{ 
        width: 100%; text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
    }}
    </style>
    <div class="logo-container">
        <img class="logo-img logo-light" src="data:image/png;base64,{logo_black_base64}">
        <img class="logo-img logo-dark" src="data:image/png;base64,{logo_h_base64}">
    </div>
    <div class='main-title'>Генератор контента</div>
    """, unsafe_allow_html=True)

# ====================== ВВОД ДАННЫХ ======================
logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = get_bg_files("images")

c1, c2, c3 = st.columns(3)

# Мы используем ключи напрямую в session_state для стабильности
with c1:
    w_mm = st.number_input("Ширина (мм)" + (" ✅" if st.session_state.get('w_val', 0) > 0 else ""), 
                           min_value=0, step=1, key='w_val')
with c2:
    h_mm = st.number_input("Высота (мм)" + (" ✅" if st.session_state.get('h_val', 0) > 0 else ""), 
                           min_value=0, step=1, key='h_val')
with c3:
    pitch = st.number_input("Шаг (мм)" + (" ✅" if st.session_state.get('p_val', 0.0) > 0 else ""), 
                            min_value=0.0, step=0.1, format="%g", key='p_val')

tw, th = 0, 0
if w_mm > 0 and h_mm > 0 and pitch > 0:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))

# Слайдер размера
default_scale = 50 if tw >= th else 40
logo_scale = st.slider("Размер лого (%)", 0, 100, default_scale)

# ====================== ПРЕВЬЮ И ЛОГИКА ======================
if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    # Отрисовка превью
    preview = process_single_image(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale, fast=True)
    if preview:
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=85)
        img_str = base64.b64encode(buf.getvalue()).decode()
        st.markdown(f'''
            <div style="display: flex; justify-content: center; margin-top: 10px;">
                <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 400px; border-radius: 8px; border: 1px solid #ddd;">
            </div>
            <div class='res-box'>Разрешение: {tw} × {th} px</div>
        ''', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Кнопки управления процессом
    btn_container = st.container()
    
    if st.session_state.zip_ready:
        current_date = datetime.now().strftime("%y_%m_%d")
        zip_filename = f"{tw}x{th}_{current_date}.zip"
        st.download_button(label="Скачать архив", data=st.session_state.zip_ready, file_name=zip_filename, mime="application/zip")
        if st.button("Сбросить"):
            st.session_state.zip_ready = None
            st.rerun()
    
    elif st.session_state.processing:
        st.button("⏳ Генерируем файлы...", disabled=True)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            with ThreadPoolExecutor() as executor:
                results = list(executor.map(lambda f: process_to_zip(f, logo_h_img, logo_v_img, tw, th, logo_scale), bg_files))
                for res in results:
                    if res: zip_file.writestr(res[0], res[1])
        
        st.session_state.zip_ready = zip_buffer.getvalue()
        st.session_state.processing = False
        st.rerun()
    
    else:
        if st.button("Создать контент"):
            st.session_state.processing = True
            st.rerun()
else:
    if not bg_files:
        st.warning("Папка 'images' пуста или не найдена.")
    else:
        st.info("Введите размеры и шаг пикселя для генерации.")
