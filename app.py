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
st.set_page_config(page_title="LED Processor", layout="wide") # Используем wide для строк

# ====================== CSS ======================
st.markdown("""
    <style>
    /* Центрируем основной контент и ограничиваем ширину */
    .block-container {
        max-width: 1000px !important;
        margin: 0 auto !important;
        padding-top: 1.5rem !important;
    }

    /* Заголовок увеличен в 2 раза */
    h1 {
        text-align: center !important;
        font-size: 2.25rem !important; /* Увеличено с 1.12rem */
        margin-bottom: 25px !important; 
    }

    /* Настройка полей ввода */
    div[data-testid="stNumberInput"], 
    div[data-testid="stSlider"] {
        width: 100% !important;
    }

    /* Стилизация блока превью и разрешения */
    .preview-block {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 20px;
    }

    /* Зеленая плашка разрешения - ширина как у превью */
    div[data-testid="stNotification"] {
        max-width: 600px !important; /* Ширина превью */
        margin: 0 auto !important;
        border-radius: 4px;
    }

    /* Центрирование кнопки */
    .centered-box {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 20px;
    }

    /* Кнопка "Скачать контент" без красной обводки */
    .stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        height: 45px !important;
        width: 190px !important;
        border-radius: 6px !important;
        border: none !important; /* Убираем обводку */
        box-shadow: none !important; /* Убираем тени */
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== ЗАГОЛОВОК ======================
st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# Контейнер для блока превью (самое верхнее положение)
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

# ====================== ВВОД ДАННЫХ В ОДНУ СТРОКУ ======================
col1, col2, col3, col4 = st.columns(4)

with col1:
    w_mm = st.number_input("Ширина (мм)", min_value=0, value=0, step=10)
with col2:
    h_mm = st.number_input("Высота (мм)", min_value=0, value=0, step=10)
with col3:
    pitch = st.number_input("Pitch (мм)", min_value=0, value=0, step=1, format="%d")
with col4:
    # Текст изменен, начальный размер 50%
    logo_percent = st.slider("Размер логотипа", 10, 80, 50, 5)

fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0

# ====================== ЛОГИКА ПРЕВЬЮ И РАЗРЕШЕНИЯ ======================
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
                preview.save(buf, format="JPEG", quality=80)
                img_str = base64.b64encode(buf.getvalue()).decode()
                # Отображение превью
                st.markdown(f'''
                    <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                        <img src="data:image/jpeg;base64,{img_str}" 
                             style="max-width: 600px; max-height: 300px; width: auto; height: auto; object-fit: contain; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    </div>
                ''', unsafe_allow_html=True)
        
        # Разрешение ПОД превью, ширина как у превью
        st.success(f"**Разрешение: {tw} × {th} px**")
        st.markdown('</div>', unsafe_allow_html=True)

# ====================== КНОПКИ СКАЧИВАНИЯ ======================
st.markdown('<div class="centered-box">', unsafe_allow_html=True)

if fields_filled:
    if st.button("Скачать контент", type="primary"): # Имя изменено
        logo_img = get_processing_logo()
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists(SOURCE_FOLDER) else []
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
            label="Сохранить ZIP файл",
            data=st.session_state.zip_data,
            file_name=st.session_state.file_name,
            mime="application/zip"
        )

st.markdown('</div>', unsafe_allow_html=True)
