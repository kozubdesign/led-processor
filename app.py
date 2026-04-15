import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps
from datetime import datetime
from functools import lru_cache

# ====================== ФУНКЦИИ ======================

@st.cache_resource
def get_cached_logo(path):
    """Загружает логотип с к��шированием"""
    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA")
        except Exception as e:
            st.warning(f"Ошибка загрузки {path}: {e}")
            return None
    return None

@st.cache_data
def get_base64_img(path):
    """Конвертирует изображение в base64"""
    if not os.path.exists(path):
        return ""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        st.error(f"Ошибка base64 конверсии {path}: {e}")
        return ""

@st.cache_data(show_spinner=False)
def get_bg_files():
    """Кеширует список фоновых изображений"""
    if not os.path.exists("images"):
        return []
    return sorted([
        os.path.join("images", f) 
        for f in os.listdir("images") 
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])

def process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent):
    """Обрабатывает одно изображение с логотипом"""
    try:
        # Выбираем логотип в зависимости от ориентации
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo:
            return None
        
        # Открываем и подгоняем фоновое изображение
        with Image.open(bg_path) as img:
            img = ImageOps.fit(
                img.convert("RGB"), 
                (tw, th), 
                Image.Resampling.LANCZOS
            )
            
            # Вычисляем размер логотипа
            lw, lh = active_logo.size
            max_scale = min(tw / lw, th / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw = max(1, int(lw * final_scale))
            new_lh = max(1, int(lh * final_scale))
            
            # Масштабируем и вставляем логотип
            logo_res = active_logo.resize(
                (new_lw, new_lh), 
                Image.Resampling.LANCZOS
            )
            img.paste(
                logo_res, 
                ((tw - new_lw) // 2, (th - new_lh) // 2), 
                logo_res
            )
            return img
    except Exception as e:
        st.error(f"Ошибка обработки {bg_path}: {e}")
        return None

def get_preview_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent):
    """Генерирует и возвращает preview в base64"""
    preview = process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent)
    if not preview:
        return None
    
    buf = io.BytesIO()
    preview.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()

def generate_zip_archive(bg_files, logo_h, logo_v, tw, th, logo_scale):
    """Генерирует ZIP архив с обработанными изображениями"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for f in bg_files:
            processed = process_single_image(f, logo_h, logo_v, tw, th, logo_scale)
            if processed:
                img_byte_arr = io.BytesIO()
                processed.save(img_byte_arr, format='JPEG', quality=95)
                zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
    return zip_buffer.getvalue()

# ====================== НАСТРОЙКА UI ======================

st.set_page_config(page_title="LED Generator", layout="wide")

# Получаем логотипы
logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")

# CSS стили
st.markdown(f"""
    <style>
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    [data-testid="stInputInstructions"] {{ display: none !important; }}
    
    div[data-baseweb="slider"] > div > div > div:nth-child(1) {{ background: #28a745 !important; }}
    div[data-baseweb="slider"] > div > div > div > div {{ background-color: #28a745 !important; }}
    div[data-testid="stThumbValue"] {{ color: black !important; font-weight: bold; }}
    
    .logo-container {{ display: flex; justify-content: center; margin: 20px 0; }}
    .logo-img {{ width: 150px; }}
    
    @media (prefers-color-scheme: light) {{ .logo-dark {{ display: none; }} .logo-light {{ display: block; }} }}
    @media (prefers-color-scheme: dark) {{ .logo-light {{ display: none; }} .logo-dark {{ display: block; }} }}
    @media (max-width: 640px) {{ .logo-img {{ width: 100px; }} }}
    
    .main-title {{ text-align: center; font-size: 1.6rem; font-weight: bold; margin-bottom: 20px; }}
    .stNumberInput, .stSlider {{ width: 100% !important; }}
    [data-testid="column"] {{ padding: 0 !important; }}
    
    div.stButton, div.stDownloadButton, div.element-container:has(button) {{
        display: flex !important; justify-content: center !important; width: 100% !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important;
    }}
    .res-box {{ 
        text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
    }}
    </style>
    
    <div class="logo-container">
        <img class="logo-img logo-light" src="data:image/png;base64,{logo_black_base64}">
        <img class="logo-img logo-dark" src="data:image/png;base64,{logo_h_base64}">
    </div>
    <div class='main-title'>LED Content Generator</div>
""", unsafe_allow_html=True)

# ====================== ЛОГИКА ======================

# Инициализация состояния
if 'zip_ready' not in st.session_state:
    st.session_state.zip_ready = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Загружаем ресурсы
logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = get_bg_files()

# Плейсхолдеры для динамического обновления
preview_placeholder = st.empty()
resolution_placeholder = st.empty()

# Ввод параметров
c1, c2, c3 = st.columns(3)
with c1:
    w_mm = st.number_input("Ширина (мм)", min_value=0, value=0)
with c2:
    h_mm = st.number_input("Высота (мм)", min_value=0, value=0)
with c3:
    pitch = st.number_input("Шаг (мм)", min_value=0.0, value=0.0, step=0.1, format="%g")

# Расчет разрешения
tw = int(round(w_mm / pitch)) if w_mm > 0 and pitch > 0 else 0
th = int(round(h_mm / pitch)) if h_mm > 0 and pitch > 0 else 0

# Слайдер масштаба логотипа
default_scale = 50 if tw >= th else 40
logo_scale = st.slider("Размер лого (%)", 0, 100, default_scale)

# Проверка валидности данных
data_valid = tw > 0 and th > 0 and (logo_h_img or logo_v_img) and bg_files

# Отображение превью
if data_valid:
    preview_base64 = get_preview_image(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale)
    if preview_base64:
        preview_placeholder.markdown(f'''
            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                <img src="data:image/jpeg;base64,{preview_base64}" 
                     style="max-width: 100%; max-height: 400px; border-radius: 8px; border: 1px solid #ddd;">
            </div>
        ''', unsafe_allow_html=True)
        resolution_placeholder.markdown(
            f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", 
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)
btn_placeholder = st.empty()

# Обработка кнопки генерации
if data_valid:
    if st.session_state.zip_ready:
        current_date = datetime.now().strftime("%y_%m_%d")
        zip_filename = f"{tw}x{th}_{current_date}.zip"
        btn_placeholder.download_button(
            label="Скачать",
            data=st.session_state.zip_ready,
            file_name=zip_filename,
            mime="application/zip"
        )
    elif st.session_state.processing:
        btn_placeholder.button("⏳ Генерируем...", disabled=True)
        st.session_state.zip_ready = generate_zip_archive(
            bg_files, logo_h_img, logo_v_img, tw, th, logo_scale
        )
        st.session_state.processing = False
        st.rerun()
    else:
        if btn_placeholder.button("Генерировать"):
            st.session_state.processing = True
            st.rerun()
