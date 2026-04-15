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
st.set_page_config(page_title="LED Processor", layout="centered")

# ====================== CSS ======================
st.markdown("""
    <style>
    /* Основной контейнер */
    .block-container {
        max-width: 600px !important;
        margin: 0 auto !important;
        padding-top: 1.5rem !important;
    }

    /* Заголовок уменьшен в 2 раза */
    h1 {
        text-align: center !important;
        font-size: 1.12rem !important;
        margin-top: 0 !important;
        margin-bottom: 20px !important; 
    }

    /* Поля ввода, слайдер и уведомления уменьшены в 2 раза (190px) */
    div[data-testid="stNumberInput"], 
    div[data-testid="stSlider"],
    div[data-testid="stNotification"] {
        margin: 0 auto 12px auto !important;
        max-width: 190px !important;
        width: 190px !important;
    }
    
    div[data-testid="stNumberInput"] input {
        text-align: left !important;
    }

    /* Кнопка в тон полям */
    .stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }
    
    .stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        height: 45px !important;
        width: 190px !important;
        min-width: 190px !important;
        border-radius: 6px !important;
        margin: 0 auto !important;
    }

    /* Уведомление (Разрешение) - подгонка стиля */
    div[data-testid="stNotification"] div {
        padding: 5px 10px !important;
        font-size: 0.85rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== ЗАГОЛОВОК ======================
st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# Контейнер для превью
preview_container = st.container()

# ====================== SESSION STATE ======================
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None
    st.session_state.file_name = None

def get_processing_logo():
    if os.path.exists(LOGO_PATH):
        try:
            return Image.open(LOGO_PATH).convert("RGBA")
        except:
            return None
    return None

def process_single_image(bg_path, logo_img, tw, th, logo_percent):
    try:
        img = Image.open(bg_path).convert("RGB")
        logo = logo_img.convert("RGBA")
        ir, tr = img.width / img.height, tw / th
        if ir < tr:
            nw, nh = tw, int(tw / ir)
        else:
            nh, nw = th, int(th * ir)
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - tw)//2, (nh - th)//2, (nw + tw)//2, (nh + th)//2))
        limit = int(min(tw, th) * (logo_percent / 100))
        lw = int(limit * (logo.width / logo.height))
        lh = int(limit * (logo.height / logo.width))
        if lw > limit:
            lw, lh = limit, int(limit * (logo.height / logo.width))
        else:
            lh, lw = limit, int(limit * (logo.width / logo.height))
        logo_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo_res, ((tw - lw)//2, (th - lh)//2), logo_res)
        return img
    except:
        return None

# ====================== ВВОД ДАННЫХ ======================
w_mm = st.number_input("Ширина (мм)", min_value=0, value=0, step=10)
h_mm = st.number_input("Высота (мм)", min_value=0, value=0, step=10)
pitch = st.number_input("Pitch (мм)", min_value=0, value=0, step=1, format="%d")
logo_percent = st.slider("Лого (%)", 10, 80, 45, 5)

fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0

# ====================== ПРЕВЬЮ ======================
if fields_filled:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))
    with preview_container:
        logo_img = get_processing_logo()
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []
        if logo_img and bg_files:
            preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), logo_img, tw, th, logo_percent)
            if preview:
                buf = io.BytesIO()
                preview.save(buf, format="JPEG", quality=80)
                img_str = base64.b64encode(buf.getvalue()).decode()
                st.markdown(f'''
                    <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                        <img src="data:image/jpeg;base64,{img_str}" 
                             style="max-width: 600px; max-height: 300px; width: auto; height: auto; object-fit: contain; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    </div>
                ''', unsafe_allow_html=True)

# ====================== ВЫВОД И КНОПКИ ======================
if fields_filled:
    st.success(f"**{tw} × {th} px**")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Создать ZIP", type="primary", use_container_width=True):
        if fields_filled:
            logo_img = get_processing_logo()
            if logo_img and bg_files:
                with st.spinner("Ждите..."):
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for i, fname in enumerate(bg_files):
                            res = process_single_image(os.path.join(SOURCE_FOLDER, fname), logo_img, tw, th, logo_percent)
                            if res:
                                b = io.BytesIO()
                                res.save(b, format="JPEG", quality=95, optimize=True)
                                zf.writestr(f"{tw}x{th}_{i+1:02d}.jpg", b.getvalue())
                    st.session_state.zip_data = zip_buffer.getvalue()
                    st.session_state.file_name = f"LED_{datetime.now().strftime('%y%m%d')}.zip"
                    st.rerun()

    if st.session_state.zip_data:
        st.download_button(
            label="Скачать файл",
            data=st.session_state.zip_data,
            file_name=st.session_state.file_name,
            mime="application/zip",
            use_container_width=True
        )
