import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

# ====================== КОНСТАНТЫ ======================
LOGO_PATH = "logo.png"
LOGO_BLACK_PATH = "logo_black.png"
FAVICON_PATH = "favicon.png"
SOURCE_FOLDER = "images"

# ====================== НАСТРОЙКА ======================
if os.path.exists(FAVICON_PATH):
    st.set_page_config(page_title="LED Processor", page_icon=FAVICON_PATH, layout="centered")
else:
    st.set_page_config(page_title="LED Processor", layout="centered")

# ====================== CSS ======================
st.markdown("""
    <style>
    .block-container {
        max-width: 720px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }

    /* Логотип - уменьшен в 2 раза по высоте (было 68px, стало 34px) */
    div[data-testid="stImage"] img {
        margin: 0 auto 30px auto !important;
        height: 34px !important;
        width: auto !important;
        display: block !important;
    }

    h1 {
        text-align: center !important;
        font-size: 2.25rem !important;
        margin-bottom: 12px !important;
    }

    .subtitle {
        text-align: center !important;
        color: #666;
        font-size: 1.05rem;
        margin-bottom: 40px !important;
    }

    .params-title {
        text-align: center !important;
        font-size: 1.35rem;
        margin: 30px 0 22px 0;
    }

    /* Поля ввода по центру с фиксированной шириной */
    div[data-testid="stNumberInput"] {
        margin: 0 auto 16px auto !important;
        max-width: 380px !important;
        width: 380px !important;
    }
    
    div[data-testid="stNumberInput"] input {
        text-align: left !important;
    }

    /* Кнопка такой же ширины как поля ввода */
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
        padding: 0 20px !important;
        border-radius: 8px !important;
        margin: 0 auto !important;
    }
    
    /* Превью - сохраняем пропорции без искажения */
    .preview-image {
        display: flex !important;
        justify-content: center !important;
        margin: 35px auto !important;
        max-width: 100%;
        height: auto;
    }
    
    .preview-image img {
        max-width: 100%;
        height: auto !important;
        width: auto !important;
        object-fit: contain;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== ЛОГОТИП ======================
is_dark = st.get_option("theme.base") == "dark"
header_logo = LOGO_PATH if is_dark else LOGO_BLACK_PATH

if os.path.exists(header_logo):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Убираем параметр width, CSS контролирует размер через height
        st.image(header_logo)

st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)
st.markdown('<p class="subtitle">Введите параметры экрана, чтобы увидеть превью</p>', unsafe_allow_html=True)

# ====================== SESSION STATE ======================
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None
    st.session_state.file_name = None

if 'uploaded_logo' not in st.session_state:
    st.session_state.uploaded_logo = None

def get_processing_logo():
    if st.session_state.uploaded_logo is not None:
        return Image.open(st.session_state.uploaded_logo).convert("RGBA")
    if os.path.exists(LOGO_PATH):
        try:
            return Image.open(LOGO_PATH).convert("RGBA")
        except:
            return None
    return None

# ====================== ОБРАБОТКА ======================
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

# ====================== САЙДБАР ======================
with st.sidebar:
    st.header("Настройки")
    st.session_state.uploaded_logo = st.file_uploader("Загрузить другой логотип", type=['png', 'jpg', 'jpeg'])
    
    if st.session_state.uploaded_logo:
        st.success("✓ Логотип загружен")
    elif os.path.exists(LOGO_PATH):
        st.info("Используется logo.png")
    
    logo_percent = st.slider("Размер логотипа (%)", 20, 70, 45, 5)

# ====================== ПАРАМЕТРЫ ======================
st.markdown('<p class="params-title">Параметры экрана</p>', unsafe_allow_html=True)

w_mm = st.number_input("Ширина экрана (мм)", min_value=0, max_value=9999999, value=0, step=10)
h_mm = st.number_input("Высота экрана (мм)", min_value=0, max_value=9999999, value=0, step=10)

# Шаг пикселя - только целые числа, без дробной части
pitch = st.number_input("Шаг пикселя (мм)", 
                       min_value=0, 
                       max_value=999999, 
                       value=0, 
                       step=1,
                       format="%d")

fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0

if fields_filled:
    tw = int(round(w_mm / pitch))
    th = int(round(h_mm / pitch))
    st.success(f"**Разрешение: {tw} × {th} px**")

# ====================== ПРЕВЬЮ (без искажения) ======================
if fields_filled:
    logo_img = get_processing_logo()
    if logo_img:
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if bg_files:
            preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), logo_img, tw, th, logo_percent)
            if preview:
                # Превью масштабируется без искажения, сохраняя пропорции
                st.markdown('<div class="preview-image">', unsafe_allow_html=True)
                st.image(preview, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

# ====================== КНОПКА ======================
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
                        zip_buffer.seek(0)
                        st.session_state.zip_data = zip_buffer.getvalue()
                        
                        # Формируем имя архива: "Контент на экран 26 04 15"
                        now = datetime.now()
                        year = now.strftime("%y")
                        month = now.strftime("%m")
                        day = now.strftime("%d")
                        st.session_state.file_name = f"Контент на экран {year} {month} {day}.zip"
                        
                        st.success("✅ Архив создан!")
                        st.rerun()  # Перезапускаем для отображения кнопки скачивания
        else:
            st.warning("Заполните все параметры экрана")

# ====================== АВТОМАТИЧЕСКОЕ СКАЧИВАНИЕ ======================
if st.session_state.zip_data is not None:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="Скачать контент",
            data=st.session_state.zip_data,
            file_name=st.session_state.file_name,
            mime="application/zip",
            type="primary",
            use_container_width=True
        )

st.caption("• Логотип по умолчанию: logo.png (можно заменить в сайдбаре)")
