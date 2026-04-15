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

st.markdown("""
    <style>
    .block-container { max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }
    .main-title { text-align: center !important; margin-bottom: 15px !important; font-size: 1.5rem !important; font-weight: bold; }
    
    div.stButton, div.stDownloadButton, div.element-container:has(button) {
        display: flex !important; justify-content: center !important; width: 100% !important;
    }
    .stButton > button, .stDownloadButton > button {
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important; border: none !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { background-color: #218838 !important; }

    .res-box { 
        text-align: center; background-color: #d4edda; color: #155724; 
        padding: 10px; border-radius: 8px; margin-bottom: 20px; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def get_cached_logo(path):
    if os.path.exists(path):
        try: return Image.open(path).convert("RGBA")
        except: return None
    return None

def process_single_image(bg_path, logo_rgba, tw, th, logo_percent):
    try:
        with Image.open(bg_path) as img:
            img = img.convert("RGB")
            ir, tr = img.width / img.height, tw / th
            nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            img = img.crop(((nw - tw)//2, (nh - th)//2, (nw + tw)//2, (nh + th)//2))
            limit = int(min(tw, th) * (logo_percent / 100))
            lw, lh = logo_rgba.size
            if max(lw, lh) > 0 and limit > 0:
                scale = limit / max(lw, lh)
                new_size = (int(lw * scale), int(lh * scale))
                logo_res = logo_rgba.resize(new_size, Image.Resampling.LANCZOS)
                img.paste(logo_res, ((tw - new_size[0])//2, (th - new_size[1])//2), logo_res)
            return img
    except: return None

# ====================== ИНТЕРФЕЙС ======================

# 1. ШАПКА (Всегда сверху)
st.markdown("<div class='main-title'>Создать контент для LED-экрана</div>", unsafe_allow_html=True)

# 2. МЕСТО ПОД ПРЕВЬЮ И РАЗРЕШЕНИЕ
preview_area = st.container()
res_area = st.container()

# Данные
logo_img = get_cached_logo(LOGO_PATH)
bg_files = [os.path.join(SOURCE_FOLDER, f) for f in os.listdir(SOURCE_FOLDER) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []

# 3. ПОЛЯ ВВОДА + ЛОГО
st.markdown("---")
col_w, col_h, col_p, col_s = st.columns([1, 1, 1, 2])
with col_w: w_mm = st.number_input("Ширина (мм)", 0, value=0, step=10)
with col_h: h_mm = st.number_input("Высота (мм)", 0, value=0, step=10)
with col_p: pitch = st.number_input("Шаг (мм)", 0, value=0, step=1)
with col_s: logo_percent = st.slider("Лого %", 0, 150, 0, 5)

# Рендеринг контента в зарезервированные области
if w_mm > 0 and h_mm > 0 and pitch > 0:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))
    
    if logo_img and bg_files:
        preview = process_single_image(bg_files[0], logo_img, tw, th, logo_percent)
        if preview:
            buf = io.BytesIO()
            preview.save(buf, format="JPEG", quality=90)
            img_str = base64.b64encode(buf.getvalue()).decode()
            
            with preview_area:
                st.markdown(f'''
                    <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                        <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 350px; border-radius: 4px; border: 1px solid #ddd;">
                    </div>
                ''', unsafe_allow_html=True)
            
            with res_area:
                st.markdown(f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)

    # 4. КНОПКА
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Обработать все изображения"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for f in bg_files:
                processed = process_single_image(f, logo_img, tw, th, logo_percent)
                if processed:
                    img_byte_arr = io.BytesIO()
                    processed.save(img_byte_arr, format='JPEG', quality=95)
                    zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
        
        st.download_button(
            label="Скачать архив",
            data=zip_buffer.getvalue(),
            file_name=f"led_{tw}x{th}_{datetime.now().strftime('%H%M')}.zip",
            mime="application/zip"
        )
