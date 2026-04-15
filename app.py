import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image
from datetime import datetime

# ====================== КОНСТАНТЫ ======================
LOGO_PATH = "logo.png"
SOURCE_FOLDER = "images"

# ====================== НАСТРОЙКА ======================
st.set_page_config(page_title="LED Processor", layout="wide")

# ИСПРАВЛЕННЫЙ CSS
st.markdown("""
    <style>
    .block-container { 
        max-width: 800px !important; 
        margin: 0 auto !important; 
        padding-top: 1rem !important; 
    }
    
    [data-testid="stHeader"] {
        display: none;
    }

    .main-title {
        text-align: center;
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 10px;
    }

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

# 1. ШАПКА
st.markdown("<div class='main-title'>Создать контент для LED-экрана</div>", unsafe_allow_html=True)

# 2. МЕСТО ПОД ПРЕВЬЮ И РАЗРЕШЕНИЕ
preview_placeholder = st.empty()
resolution_placeholder = st.empty()

@st.cache_resource
def get_cached_logo(path):
    if os.path.exists(path):
        try: return Image.open(path).convert("RGBA")
        except: return None
    return None

def process_single_image(bg_path, logo_rgba, tw, th, user_scale_percent):
    try:
        with Image.open(bg_path) as img:
            img = img.convert("RGB")
            ir, tr = img.width / img.height, tw / th
            nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            img = img.crop(((nw - tw)//2, (nh - th)//2, (nw + tw)//2, (nh + th)//2))
            
            # БАЗОВОЕ ПРАВИЛО: 65% ширины или 30% высоты (что меньше)
            base_limit = min(tw * 0.65, th * 0.30)
            
            # КОРРЕКТИРОВКА БЕГУНКОМ (user_scale_percent / 100)
            final_limit = int(base_limit * (user_scale_percent / 100))
            
            lw, lh = logo_rgba.size
            if max(lw, lh) > 0 and final_limit > 0:
                scale = final_limit / max(lw, lh)
                new_size = (int(lw * scale), int(lh * scale))
                logo_res = logo_rgba.resize(new_size, Image.Resampling.LANCZOS)
                img.paste(logo_res, ((tw - new_size[0])//2, (th - new_size[1])//2), logo_res)
            return img
    except: return None

logo_img = get_cached_logo(LOGO_PATH)
bg_files = [os.path.join(SOURCE_FOLDER, f) for f in os.listdir(SOURCE_FOLDER) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []

# 3. ПОЛЯ ВВОДА
st.markdown("---")
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
with c1: w_mm = st.number_input("Ширина (мм)", 0, value=0)
with c2: h_mm = st.number_input("Высота (мм)", 0, value=0)
with c3: pitch = st.number_input("Шаг (мм)", 0, value=0)
# Бегунок возвращен. 100% = точное соответствие твоему правилу.
with c4: logo_scale = st.slider("Размер лого (%)", 0, 200, 100)

# ЛОГИКА ОТОБРАЖЕНИЯ ПРЕВЬЮ
tw, th = 0, 0
if w_mm > 0 and h_mm > 0 and pitch > 0:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))
    if logo_img and bg_files:
        preview = process_single_image(bg_files[0], logo_img, tw, th, logo_scale)
        if preview:
            buf = io.BytesIO()
            preview.save(buf, format="JPEG", quality=90)
            img_str = base64.b64encode(buf.getvalue()).decode()
            preview_placeholder.markdown(f'''
                <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                    <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 400px; border-radius: 8px; border: 1px solid #ddd;">
                </div>
            ''', unsafe_allow_html=True)
            resolution_placeholder.markdown(f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)

# 4. КНОПКИ И ПРОЦЕСС
st.markdown("<br>", unsafe_allow_html=True)
button_placeholder = st.empty()

if w_mm > 0 and h_mm > 0 and pitch > 0:
    if button_placeholder.button("Создать контент"):
        button_placeholder.empty()
        with st.spinner("Создание контента..."):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for f in bg_files:
                    processed = process_single_image(f, logo_img, tw, th, logo_scale)
                    if processed:
                        img_byte_arr = io.BytesIO()
                        processed.save(img_byte_arr, format='JPEG', quality=95)
                        zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
            
            st.download_button(
                label="📥 Скачать контент",
                data=zip_buffer.getvalue(),
                file_name=f"led_{tw}x{th}.zip",
                mime="application/zip"
            )
