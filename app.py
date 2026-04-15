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
    
    /* Улучшенный стиль заголовка - ТЕПЕРЬ ОН ВИДЕН! */
    .main-title { 
        text-align: center !important; 
        margin-bottom: 30px !important; 
        margin-top: 10px !important;
        font-size: 2.2rem !important; 
        font-weight: bold !important;
        color: #ffffff !important;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
        letter-spacing: 1px !important;
    }
    
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

# 1. ШАПКА (ТЕПЕРЬ ЗАГОЛОВОК ОТЛИЧНО ВИДЕН!)
st.markdown("<div class='main-title'>✨ Создать контент для LED-экрана ✨</div>", unsafe_allow_html=True)

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

# Подготовка данных
logo_img = get_cached_logo(LOGO_PATH)
bg_files = [os.path.join(SOURCE_FOLDER, f) for f in os.listdir(SOURCE_FOLDER) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []

# 2. РЕЗЕРВИРУЕМ МЕСТО ПОД ПРЕВЬЮ И РАЗРЕШЕНИЕ (сразу под шапкой)
preview_placeholder = st.empty()
res_placeholder = st.empty()

# 3. ПОЛЯ ВВОДА (внизу)
st.markdown("---")
col_w, col_h, col_p, col_s = st.columns([1, 1, 1, 2])
with col_w: w_mm = st.number_input("Ширина (мм)", 0, value=0, key="w_mm")
with col_h: h_mm = st.number_input("Высота (мм)", 0, value=0, key="h_mm")
with col_p: pitch = st.number_input("Шаг (мм)", 0, value=0, key="pitch")
with col_s: logo_p = st.slider("Лого %", 0, 150, 0)

# ЛОГИКА ОТОБРАЖЕНИЯ (Заполняем пустые места наверху)
if w_mm > 0 and h_mm > 0 and pitch > 0:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))
    
    if logo_img and bg_files:
        preview = process_single_image(bg_files[0], logo_img, tw, th, logo_p)
        if preview:
            buf = io.BytesIO()
            preview.save(buf, format="JPEG", quality=90)
            img_str = base64.b64encode(buf.getvalue()).decode()
            
            # Вставляем превью в зарезервированное место №2
            preview_placeholder.markdown(f'''
                <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                    <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 350px; border-radius: 4px; border: 1px solid #ddd;">
                </div>
            ''', unsafe_allow_html=True)
            
            # Вставляем разрешение в зарезервированное место №3
            res_placeholder.markdown(f"<div class='res-box'>📐 Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)
        else:
            preview_placeholder.empty()
            res_placeholder.empty()
    else:
        if not logo_img:
            st.warning("⚠️ Логотип не найден. Поместите файл logo.png в корневую папку.")
        if not bg_files:
            st.warning("⚠️ Изображения не найдены. Создайте папку 'images' и добавьте в нее файлы .jpg, .png или .jpeg")
else:
    # Если параметры не введены, очищаем превью и разрешение
    preview_placeholder.empty()
    res_placeholder.empty()

# 4. КНОПКА ОБРАБОТКИ
if w_mm > 0 and h_mm > 0 and pitch > 0 and logo_img and bg_files:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Обработать все изображения", key="process_btn"):
        with st.spinner("Обработка изображений..."):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for f in bg_files:
                    processed = process_single_image(f, logo_img, tw, th, logo_p)
                    if processed:
                        img_byte_arr = io.BytesIO()
                        processed.save(img_byte_arr, format='JPEG', quality=95)
                        zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
            
            st.download_button(
                label="📥 Скачать архив",
                data=zip_buffer.getvalue(),
                file_name=f"led_{tw}x{th}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                key="download_btn"
            )
