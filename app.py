import streamlit as st
import zipfile
import io
import os
import base64
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
        max-width: 800px !important; /* Увеличено для превью шириной 800px */
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }

    /* Логотип - исправлена обрезка (object-fit) и уменьшен отступ (10px) */
    div[data-testid="stImage"] img {
        margin: 0 auto 10px auto !important; 
        height: 34px !important;
        width: auto !important;
        object-fit: contain !important; 
        display: block !important;
    }

    h1 {
        text-align: center !important;
        font-size: 2.25rem !important;
        margin-top: 0 !important;
        margin-bottom: 30px !important; 
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
    </style>
    """, unsafe_allow_html=True)

# ====================== ЛОГОТИП И ЗАГОЛОВОК ======================
is_dark = st.get_option("theme.base") == "dark"
header_logo = LOGO_PATH if is_dark else LOGO_BLACK_PATH

if os.path.exists(header_logo):
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(header_logo)

st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# ====================== КОНТЕЙНЕР ДЛЯ ПРЕВЬЮ НАД ПОЛЯМИ ======================
preview_container = st.container()

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

# ====================== ОБРАБОТКА ИЗОБРАЖЕНИЯ ======================
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
    except Exception as e:
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

# ====================== ПАРАМЕТРЫ ЭКРАНА ======================
w_mm = st.number_input("Ширина экрана (мм)", min_value=0, max_value=9999999, value=0, step=10)
h_mm = st.number_input("Высота экрана (мм)", min_value=0, max_value=9999999, value=0, step=10)
pitch = st.number_input("Шаг пикселя (мм)", min_value=0, max_value=999999, value=0, step=1, format="%d")

fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0

# ====================== ГЕНЕРАЦИЯ ПРЕВЬЮ В ВЕРХНИЙ КОНТЕЙНЕР ======================
if fields_filled:
    tw = int(round(w_mm / pitch))
    th = int(round(h_mm / pitch))
    
    # Отрисовываем контент внутри заранее созданного контейнера
    with preview_container:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.success(f"**Разрешение: {tw} × {th} px**")
            
        logo_img = get_processing_logo()
        if logo_img:
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if bg_files:
                preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), logo_img, tw, th, logo_percent)
                if preview:
                    # Конвертируем превью в Base64 для точного контроля размеров через HTML
                    buf = io.BytesIO()
                    preview.save(buf, format="JPEG", quality=85)
                    img_str = base64.b64encode(buf.getvalue()).decode()
                    
                    st.markdown(f'''
                        <div style="display: flex; justify-content: center; align-items: center; width: 100%; margin-bottom: 30px;">
                            <img src="data:image/jpeg;base64,{img_str}" 
                                 style="max-width: 800px; max-height: 400px; width: auto; height: auto; object-fit: contain; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                        </div>
                    ''', unsafe_allow_html=True)

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
                        
                        now = datetime.now()
                        year = now.strftime("%y")
                        month = now.strftime("%m")
                        day = now.strftime("%d")
                        st.session_state.file_name = f"Контент на экран {year} {month} {day}.zip"
                        
                        st.success("✅ Архив создан!")
                        st.rerun() 
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
