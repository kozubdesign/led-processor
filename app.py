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
    .block-container {
        max-width: 800px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }

    h1 {
        text-align: center !important;
        font-size: 2.25rem !important;
        margin-top: 0 !important;
        margin-bottom: 30px !important; 
    }

    /* Поля ввода и слайдер по центру */
    div[data-testid="stNumberInput"], div[data-testid="stSlider"] {
        margin: 0 auto 16px auto !important;
        max-width: 380px !important;
        width: 380px !important;
    }
    
    div[data-testid="stNumberInput"] input {
        text-align: left !important;
    }

    /* Кнопка */
    .stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin: 10px 0 20px 0 !important;
    }
    
    .stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.12rem !important;
        height: 54px !important;
        width: 380px !important;
        min-width: 380px !important;
        border-radius: 8px !important;
        margin: 0 auto !important;
    }

    /* Плашка разрешения */
    div[data-testid="stNotification"] {
        max-width: 380px !important;
        margin: 0 auto 15px auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== ЗАГОЛОВОК ======================
st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# Контейнер для превью в самом верху
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

# ====================== ОБРАБОТКА ======================
def process_single_image(bg_path, logo_img, tw, th, logo_percent):
    try:
        img = Image.open(bg_path).convert("RGB")
        logo = logo_img.convert("RGBA")

        ir = img.width / img.height
        tr = tw / th
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
            lw = limit
            lh = int(lw * (logo.height / logo.width))
        else:
            lh = limit
            lw = int(lh * (logo.width / logo.height))

        logo_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo_res, ((tw - lw)//2, (th - lh)//2), logo_res)
        return img
    except:
        return None

# ====================== ВВОД ДАННЫХ ======================
w_mm = st.number_input("Ширина экрана (мм)", min_value=0, value=0, step=10)
h_mm = st.number_input("Высота экрана (мм)", min_value=0, value=0, step=10)
pitch = st.number_input("Шаг пикселя (мм)", min_value=0, value=0, step=1, format="%d")
logo_percent = st.slider("Размер логотипа (%)", 10, 80, 45, 5)

fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0

# ====================== ЛОГИКА ПРЕВЬЮ ======================
if fields_filled:
    tw = int(round(w_mm / pitch))
    th = int(round(h_mm / pitch))
    
    with preview_container:
        logo_img = get_processing_logo()
        if logo_img:
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if bg_files:
                preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), logo_img, tw, th, logo_percent)
                if preview:
                    buf = io.BytesIO()
                    preview.save(buf, format="JPEG", quality=85)
                    img_str = base64.b64encode(buf.getvalue()).decode()
                    
                    st.markdown(f'''
                        <div style="display: flex; justify-content: center; margin-bottom: 30px;">
                            <img src="data:image/jpeg;base64,{img_str}" 
                                 style="max-width: 800px; max-height: 400px; width: auto; height: auto; object-fit: contain; border-radius: 4px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                        </div>
                    ''', unsafe_allow_html=True)

# ====================== ВЫВОД РАЗРЕШЕНИЯ И КНОПКА ======================
if fields_filled:
    st.success(f"**Разрешение: {tw} × {th} px**")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("Скачать контент", type="primary", use_container_width=True):
        if fields_filled:
            logo_img = get_processing_logo()
            if logo_img:
                with st.spinner("Обработка..."):
                    bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    if bg_files:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                            for i, fname in enumerate(bg_files):
                                res = process_single_image(os.path.join(SOURCE_FOLDER, fname), logo_img, tw, th, logo_percent)
                                if res:
                                    buf = io.BytesIO()
                                    res.save(buf, format="JPEG", quality=95, optimize=True)
                                    zf.writestr(f"{tw}x{th}_{i+1:02d}.jpg", buf.getvalue())
                        
                        st.session_state.zip_data = zip_buffer.getvalue()
                        now = datetime.now()
                        st.session_state.file_name = f"Контент {now.strftime('%y %m %d')}.zip"
                        st.rerun() 
        else:
            st.warning("Заполните параметры экрана")

# Кнопка скачивания архива
if st.session_state.zip_data is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="Нажмите для сохранения ZIP",
            data=st.session_state.zip_data,
            file_name=st.session_state.file_name,
            mime="application/zip",
            use_container_width=True
        )
