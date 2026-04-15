import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps
from datetime import datetime

# ====================== ФУНКЦИИ ОБРАБОТКИ ======================
@st.cache_resource
def get_cached_logo(path):
    if os.path.exists(path):
        try: return Image.open(path).convert("RGBA")
        except: return None
    return None

def get_base64_img(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        except: return ""
    return ""

def process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent, w_mm, h_mm):
    try:
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo: return None
        with Image.open(bg_path) as img:
            temp_aspect = w_mm / h_mm
            temp_h = 1200
            temp_w = int(temp_h * temp_aspect)
            img = ImageOps.fit(img.convert("RGB"), (temp_w, temp_h), Image.Resampling.LANCZOS)
            lw, lh = active_logo.size
            max_scale = min(temp_w / lw, temp_h / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
            img.paste(logo_res, ((temp_w - new_lw)//2, (temp_h - new_lh)//2), logo_res)
            return img.resize((tw, th), Image.Resampling.LANCZOS)
    except: return None

# ====================== UI И СТИЛИ ======================
st.set_page_config(page_title="LEDsi Генератор контента", layout="wide", page_icon="favicon.png")

logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")

st.markdown(f"""
    <style>
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}

    /* СТИЛЬ КНОПКИ ГЕНЕРАЦИИ (ЗЕЛЕНАЯ) */
    .stButton > button {{
        width: 100% !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: bold !important; border-radius: 8px !important;
    }}

    /* СТИЛЬ КНОПКИ СКАЧИВАНИЯ (СИНЯЯ - ЧТОБЫ ЗАМЕТИТЬ) */
    .stDownloadButton > button {{
        width: 100% !important; height: 60px !important; background-color: #007bff !important;
        color: white !important; font-weight: 800 !important; border-radius: 8px !important;
        border: 2px solid #0056b3 !important; font-size: 1.2rem !important;
    }}

    /* iOS СПИННЕР */
    button[disabled] p::before {{
        content: ""; display: inline-block; width: 20px; height: 20px;
        margin-right: 12px; vertical-align: middle; border-radius: 50%;
        background: conic-gradient(from 0deg, transparent 0%, #ffffff 100%);
        mask: radial-gradient(farthest-side, transparent 65%, black 70%);
        -webkit-mask: radial-gradient(farthest-side, transparent 65%, black 70%);
        animation: spin 1s steps(12) infinite;
    }}
    
    .res-box {{ 
        text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
    }}
    </style>
    
    <div style="text-align:center; margin-bottom:20px;">
        <img src="data:image/png;base64,{logo_h_base64}" style="width:150px;">
        <h2 style="margin-top:10px;">Генератор контента</h2>
    </div>
    """, unsafe_allow_html=True)

# ====================== ЛОГИКА ПРИЛОЖЕНИЯ ======================
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

# Загрузка ресурсов
logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = [os.path.join("images", f) for f in os.listdir("images") 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []

# Ввод параметров
c1, c2, c3 = st.columns(3)
with c1: w_mm = st.number_input("Ширина (мм)", 0, value=8000)
with c2: h_mm = st.number_input("Высота (мм)", 0, value=6000)
with c3: pitch_str = st.text_input("Шаг (мм)", value="16/32")

# Расчет разрешения
tw, th, pitch_x, pitch_y = 0, 0, 0.0, 0.0
try:
    if "/" in pitch_str:
        parts = pitch_str.split("/")
        pitch_x, pitch_y = float(parts[0]), float(parts[1])
    else:
        pitch_x = pitch_y = float(pitch_str)
    if pitch_x > 0 and pitch_y > 0:
        tw, th = int(round(w_mm / pitch_x)), int(round(h_mm / pitch_y))
except: pass

logo_scale = st.slider("Размер лого (%)", 0, 100, 50)

# Превью и разрешение
if tw > 0 and bg_files:
    st.markdown(f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)
    st.info(f"Найдено изображений в папке: {len(bg_files)}")

st.markdown("---")
btn_container = st.empty()

# ЛОГИКА КНОПОК
if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    # 1. Если архив готов — показываем БОЛЬШУЮ СИНЮЮ КНОПКУ
    if st.session_state.zip_ready:
        current_date = datetime.now().strftime("%y_%m_%d")
        zip_filename = f"{tw}x{th}_{current_date}.zip"
        st.download_button(
            label="🚀 СКАЧАТЬ ГОТОВЫЙ АРХИВ", 
            data=st.session_state.zip_ready, 
            file_name=zip_filename, 
            mime="application/zip",
            key="download_btn"
        )
        if st.button("♻️ Создать заново"):
            st.session_state.zip_ready = None
            st.rerun()

    # 2. Если в процессе — крутим спиннер и бар
    elif st.session_state.processing:
        btn_container.button("Генерация...", disabled=True)
        bar = st.progress(0)
        status = st.empty()
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, f in enumerate(bg_files):
                processed = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
                if processed:
                    img_io = io.BytesIO()
                    processed.save(img_io, format='JPEG', quality=95)
                    zip_file.writestr(os.path.basename(f), img_io.getvalue())
                bar.progress((i + 1) / len(bg_files))
                status.center(f"Обработка: {i+1} из {len(bg_files)}")
        
        st.session_state.zip_ready = zip_buffer.getvalue()
        st.session_state.processing = False
        st.rerun()

    # 3. Исходное состояние
    else:
        if btn_container.button("Сгенерировать контент"):
            st.session_state.zip_ready = None
            st.session_state.processing = True
            st.rerun()
