import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

# --- КОНСТАНТЫ ---
DEFAULT_LOGO_PATH = "logo.png"
HEADER_LOGO_PATH = "logo_header.png"   # ← положи сюда свой треугольный логотип (цветной)
SOURCE_FOLDER = "images"

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="LED Processor", layout="centered")

# --- УСИЛЕННЫЙ CSS ДЛЯ ЦЕНТРОВКИ ---
st.markdown("""
    <style>
    .block-container {
        max-width: 760px !important;
        margin: 0 auto !important;
        padding-top: 1.5rem !important;
    }
    
    /* Логотип в шапке */
    .header-logo {
        display: block;
        margin: 0 auto 1rem auto;
        height: 70px;
        object-fit: contain;
    }
    
    h1 {
        text-align: center !important;
        font-size: 2.15rem !important;
        margin: 0.5rem 0 0.3rem 0 !important;
    }
    
    .subtitle {
        text-align: center !important;
        color: #555;
        font-size: 1.05rem;
        margin-bottom: 2rem !important;
    }
    
    /* Параметры экрана */
    .section-title {
        text-align: center !important;
        font-size: 1.35rem;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* Все поля ввода по центру */
    div[data-testid="stNumberInput"] {
        margin: 0 auto 1rem auto !important;
        max-width: 340px !important;
    }
    
    /* Ещё уже поле для шага пикселя */
    .step-input {
        max-width: 210px !important;
        margin: 0 auto 1.5rem auto !important;
    }
    
    /* Зелёная кнопка по центру и компактная */
    .stButton {
        display: flex !important;
        justify-content: center !important;
    }
    .stButton > button {
        height: 3.6rem !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        background-color: #28a745 !important;
        color: white !important;
        min-width: 300px !important;
        padding: 0 40px !important;
        border-radius: 8px !important;
    }
    
    [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        margin: 2rem auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГОТИП ВВЕРХУ ---
if os.path.exists(HEADER_LOGO_PATH):
    st.image(HEADER_LOGO_PATH, use_container_width=False, width=180)
elif os.path.exists(DEFAULT_LOGO_PATH):
    st.image(DEFAULT_LOGO_PATH, use_container_width=False, width=180)

st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Введите параметры экрана, чтобы увидеть превью</p>', unsafe_allow_html=True)

# --- SESSION STATE ---
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None
    st.session_state.file_name = None

if 'uploaded_logo' not in st.session_state:
    st.session_state.uploaded_logo = None

def get_logo_for_processing():
    if st.session_state.uploaded_logo is not None:
        return Image.open(st.session_state.uploaded_logo).convert("RGBA")
    if os.path.exists(DEFAULT_LOGO_PATH):
        try:
            return Image.open(DEFAULT_LOGO_PATH).convert("RGBA")
        except:
            return None
    return None

# --- ФУНКЦИЯ ОБРАБОТКИ (без изменений) ---
def process_single_image(bg_path, logo_img, tw, th, logo_percent=45):
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

# --- САЙДБАР ---
with st.sidebar:
    st.header("Настройки")
    st.session_state.uploaded_logo = st.file_uploader("Загрузить другой логотип", type=['png', 'jpg', 'jpeg'])
    if st.session_state.uploaded_logo:
        st.success("✓ Логотип загружен")
    elif os.path.exists(DEFAULT_LOGO_PATH):
        st.info("Используется logo.png")
    
    logo_percent = st.slider("Размер логотипа (%)", 20, 70, 45, 5)

# --- ПАРАМЕТРЫ ЭКРАНА ---
st.markdown('<p class="section-title">Параметры экрана</p>', unsafe_allow_html=True)

col1, col_mid, col2 = st.columns([1, 0.1, 1])
with col1:
    w_mm = st.number_input("Ширина экрана (мм)", min_value=0, max_value=9999999, value=0, step=10)
with col2:
    h_mm = st.number_input("Высота экрана (мм)", min_value=0, max_value=9999999, value=0, step=10)

# Узкое поле шага пикселя
pitch = st.number_input(
    "Шаг пикселя (мм)", 
    min_value=0.0, 
    max_value=999.99999, 
    value=0.0, 
    format="%.5f", 
    step=0.00001
)

fields_filled = w_mm > 0 and h_mm > 0 and pitch >= 0.00001

if fields_filled:
    tw = int(round(w_mm / pitch))
    th = int(round(h_mm / pitch))
    st.success(f"**Разрешение: {tw} × {th} px**")

# --- ПРЕВЬЮ ---
if fields_filled:
    logo_img = get_logo_for_processing()
    if logo_img:
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if bg_files:
            preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), logo_img, tw, th, logo_percent)
            if preview:
                scale = min(800 / tw, 400 / th, 1.0)
                st.image(preview, width=int(tw * scale), caption=f"Превью — {bg_files[0]}")

# --- КНОПКА ---
if st.button("🚀 Создать архив с контентом", type="primary"):
    if fields_filled:
        logo_img = get_logo_for_processing()
        if logo_img:
            with st.spinner("Создаём архив..."):
                bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if not bg_files:
                    st.error("Нет изображений в папке images")
                else:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for i, f in enumerate(bg_files):
                            res = process_single_image(os.path.join(SOURCE_FOLDER, f), logo_img, tw, th, logo_percent)
                            if res:
                                buf = io.BytesIO()
                                res.save(buf, format="JPEG", quality=95, optimize=True)
                                zf.writestr(f"{tw}x{th}_{i+1:02d}.jpg", buf.getvalue())
                    zip_buffer.seek(0)
                    st.session_state.zip_data = zip_buffer.getvalue()
                    st.session_state.file_name = f"LED_{tw}x{th}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                    st.success("✅ Архив успешно создан!")
    else:
        st.warning("Пожалуйста, заполните все параметры")

# --- СКАЧИВАНИЕ ---
if st.session_state.zip_data is not None:
    st.download_button(
        label="💾 Скачать ZIP-архив",
        data=st.session_state.zip_data,
        file_name=st.session_state.file_name,
        mime="application/zip",
        type="primary"
    )

st.caption("• Логотип по умолчанию: logo.png (можно заменить в сайдбаре)")
