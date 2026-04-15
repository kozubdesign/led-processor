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

# ====================== УЛЬТИМАТИВНЫЙ CSS ======================
st.markdown("""
    <style>
    /* Центрирование контента */
    .block-container {
        max-width: 1000px !important;
        margin: 0 auto !important;
        padding-top: 1.5rem !important;
    }

    /* Заголовок */
    h1 {
        text-align: center !important;
        font-size: 2.25rem !important;
        margin-bottom: 25px !important; 
        width: 100% !important;
    }

    /* Превью и разрешение */
    .preview-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 20px;
        width: 100%;
    }

    /* Зеленая плашка разрешения */
    div[data-testid="stNotification"] {
        max-width: 600px !important;
        margin: 0 auto !important;
    }
    
    div[data-testid="stNotification"] div[role="alert"] {
        justify-content: center !important;
        text-align: center !important;
    }

    /* Принудительная зеленая обводка полей ввода */
    div[data-testid="stNumberInput"] input {
        border-color: #28a745 !important;
        box-shadow: 0 0 0 1px #28a745 !important;
    }

    /* КНОПКА СТРОГО ПО ЦЕНТРУ СТРАНИЦЫ (ПОД ЗАГОЛОВКОМ) */
    div.stButton, div[data-testid="stDownloadButton"] {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin-top: 30px !important;
    }

    .stButton > button, div[data-testid="stDownloadButton"] > button {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: 600 !important;
        height: 52px !important;
        width: 300px !important; /* Фиксированная ширина для симметрии */
        border-radius: 8px !important;
        border: none !important;
        margin: 0 auto !important; /* Центрирование внутри флекс-контейнера */
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== ЗАГОЛОВОК ======================
st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

preview_block_container = st.container()

# ====================== SESSION STATE ======================
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None
    st.session_state.file_name = None

def get_processing_logo():
    if os.path.exists(LOGO_PATH):
        try: return Image.open(LOGO_PATH).convert("RGBA")
        except: return None
    return None

def process_single_image(bg_path, logo_img, tw, th, logo_percent):
    try:
        img = Image.open(bg_path).convert("RGB")
        logo = logo_img.convert("RGBA")
        ir, tr = img.width / img.height, tw / th
        if ir < tr: nw, nh = tw, int(tw / ir)
        else: nh, nw = th, int(th * ir)
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - tw)//2, (nh - th)//2, (nw + tw)//2, (nh + th)//2))
        
        limit = int(min(tw, th) * (logo_percent / 100))
        lw = int(limit * (logo.width / logo.height))
        lh = int(limit * (logo.height / logo.width))
        if lw > limit: lw, lh = limit, int(limit * (logo.height / logo.width))
        else: lh, lw = limit, int(limit * (logo.width / logo.height))
        
        logo_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo_res, ((tw - lw)//2, (th - lh)//2), logo_res)
        return img
    except: return None

# ====================== ВВОД ДАННЫХ ======================
col_w, col_h, col_p, col_s = st.columns([2, 2, 2, 3])

with col_w:
    w_mm = st.number_input("Ширина (мм)", min_value=0, value=0, step=10)
with col_h:
    h_mm = st.number_input("Высота (мм)", min_value=0, value=0, step=10)
with col_p:
    pitch = st.number_input("Шаг пикселя (мм)", min_value=0, value=0, step=1)
with col_s:
    logo_percent = st.slider("Размер логотипа в %", 0, 150, 60, 5)

fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0

# ====================== ПРЕВЬЮ И РАЗРЕШЕНИЕ ======================
if fields_filled:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))
    with preview_block_container:
        st.markdown('<div class="preview-block">', unsafe_allow_html=True)
        logo_img = get_processing_logo()
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []
        
        if logo_img and bg_files:
            preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), logo_img, tw, th, logo_percent)
            if preview:
                buf = io.BytesIO()
                preview.save(buf, format="JPEG", quality=100)
                img_str = base64.b64encode(buf.getvalue()).decode()
                st.markdown(f'''
                    <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                        <img src="data:image/jpeg;base64,{img_str}" 
                             style="max-width: 600px; max-height: 300px; width: auto; height: auto; object-fit: contain; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    </div>
                ''', unsafe_allow_html=True)
        st.success(f"**Разрешение: {tw} × {th} px**")
        st.markdown('</div>', unsafe_allow_html=True)

# ====================== ЛОГИКА КНОПОК ======================
# Кнопки НЕ в колонках — это гарантирует центрирование по всей ширине страницы
if fields_filled:
    if st.session_state.zip_data is None:
        if st.button("Генерировать контент"):
            logo_img = get_processing_logo()
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []
            if logo_img and bg_files:
                with st.spinner("Генерация..."):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for i, fname in enumerate(bg_files):
                            res = process_single_image(os.path.join(SOURCE_FOLDER, fname), logo_img, tw, th, logo_percent)
                            if res:
                                b = io.BytesIO()
                                res.save(b, format="JPEG", quality=100, subsampling=0)
                                zf.writestr(f"{tw}x{th}_{i+1:02d}.jpg", b.getvalue())
                    st.session_state.zip_data = zip_buffer.getvalue()
                    st.session_state.file_name = f"LED_{datetime.now().strftime('%y%m%d')}.zip"
                    st.rerun()
    else:
        st.download_button(
            label="Скачать архив",
            data=st.session_state.zip_data,
            file_name=st.session_state.file_name,
            mime="application/zip"
        )
