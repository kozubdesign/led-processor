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

# МАКСИМАЛЬНО ЖЕСТКИЙ CSS ДЛЯ ЦЕНТРИРОВАНИЯ
st.markdown("""
    <style>
    /* Ограничение ширины основного контейнера */
    .block-container {
        max-width: 800px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }

    /* Заголовок по центру */
    h1 { text-align: center !important; margin-bottom: 2rem !important; }

    /* Центрирование плашки разрешения */
    div[data-testid="stNotification"] {
        max-width: 600px !important;
        margin: 0 auto !important;
    }
    div[data-testid="stNotification"] div[role="alert"] {
        justify-content: center !important;
    }

    /* Центрирование кнопок Генерировать и Скачать */
    .stButton, div[data-testid="stDownloadButton"] {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin-top: 20px !important;
    }

    .stButton > button, div[data-testid="stDownloadButton"] > button {
        width: 300px !important;
        height: 52px !important;
        background-color: #28a745 !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
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
            # Ресайз фона
            ir, tr = img.width / img.height, tw / th
            nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            img = img.crop(((nw - tw)//2, (nh - th)//2, (nw + tw)//2, (nh + th)//2))
            
            # Ресайз лого
            limit = int(min(tw, th) * (logo_percent / 100))
            lw, lh = logo_rgba.size
            scale = limit / max(lw, lh)
            new_size = (int(lw * scale), int(lh * scale))
            
            logo_res = logo_rgba.resize(new_size, Image.Resampling.LANCZOS)
            img.paste(logo_res, ((tw - new_size[0])//2, (th - new_size[1])//2), logo_res)
            return img
    except: return None

# ====================== ЛОГИКА ======================
st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

logo_img = get_cached_logo(LOGO_PATH)
bg_files = [os.path.join(SOURCE_FOLDER, f) for f in os.listdir(SOURCE_FOLDER) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []

# Ввод данных
col_w, col_h, col_p, col_s = st.columns([1, 1, 1, 2])
with col_w: w_mm = st.number_input("Ширина (мм)", 0, step=10)
with col_h: h_mm = st.number_input("Высота (мм)", 0, step=10)
with col_p: pitch = st.number_input("Шаг (мм)", 0, step=1)
with col_s: logo_percent = st.slider("Лого %", 0, 150, 60, 5)

if w_mm > 0 and h_mm > 0 and pitch > 0 and logo_img and bg_files:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))
    
    # Превью
    preview = process_single_image(bg_files[0], logo_img, tw, th, logo_percent)
    if preview:
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=90)
        img_str = base64.b64encode(buf.getvalue()).decode()
        st.markdown(f'''
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 300px; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
            </div>
        ''', unsafe_allow_html=True)
    
    st.success(f"**Разрешение: {tw} × {th} px**")

    # Управление состоянием архива в session_state для корректного отображения кнопок
    if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None

    if st.button("Генерировать контент"):
        with st.spinner("Сборка архива..."):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, path in enumerate(bg_files):
                    res = process_single_image(path, logo_img, tw, th, logo_percent)
                    if res:
                        b = io.BytesIO()
                        res.save(b, format="JPEG", quality=95)
                        zf.writestr(f"{tw}x{th}_{i+1:02d}.jpg", b.getvalue())
            st.session_state.zip_ready = zip_buffer.getvalue()
            st.rerun()

    if st.session_state.zip_ready:
        st.download_button(
            label="Скачать архив",
            data=st.session_state.zip_ready,
            file_name=f"LED_{datetime.now().strftime('%y%m%d')}.zip",
            mime="application/zip"
        )
else:
    if not bg_files: st.error(f"Папка '{SOURCE_FOLDER}' пуста или не найдена.")
    if not logo_img: st.error(f"Файл '{LOGO_PATH}' не найден.")
