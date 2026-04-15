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
        max-width: 740px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }

    .main-logo {
        display: block;
        margin: 0 auto 25px auto;
        height: 65px;
        object-fit: contain;
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
        margin: 25px 0 20px 0;
    }

    div[data-testid="stNumberInput"] {
        margin: 0 auto 14px auto !important;
        max-width: 340px !important;
    }

    .step-input {
        max-width: 220px !important;
        margin: 0 auto 30px auto !important;
    }

    .stButton {
        display: flex !important;
        justify-content: center !important;
        margin-top: 20px !important;
    }
    .stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.12rem !important;
        height: 54px !important;
        min-width: 320px !important;
        padding: 0 50px !important;
        border-radius: 8px !important;
    }

    [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        margin: 35px auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== ЛОГОТИП ======================
is_dark = st.get_option("theme.base") == "dark"
header_logo = LOGO_PATH if is_dark else LOGO_BLACK_PATH

if os.path.exists(header_logo):
    st.image(header_logo, use_container_width=False, width=180)

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

c1, c2 = st.columns(2)
with c1:
    w_mm = st.number_input("Ширина экрана (мм)", min_value=0, max_value=9999999, value=0, step=10)
with c2:
    h_mm = st.number_input("Высота экрана (мм)", min_value=0, max_value=9999999, value=0, step=10)

pitch = st.number_input("Шаг пикселя (мм)", 
                       min_value=0.0, 
                       max_value=999.99999, 
                       value=0.0, 
                       format="%.5f", 
                       step=0.00001)

fields_filled = w_mm > 0 and h_mm > 0 and pitch >= 0.00001

if fields_filled:
    tw = int(round(w_mm / pitch))
    th = int(round(h_mm / pitch))
    st.success(f"**Разрешение: {tw} × {th} px**")

# ====================== ПРЕВЬЮ ======================
if fields_filled:
    logo_img = get_processing_logo()
    if logo_img:
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if bg_files:
            preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), logo_img, tw, th, logo_percent)
            if preview:
                scale = min(800 / tw, 400 / th, 1.0)
                st.image(preview, width=int(tw * scale))

# ====================== КНОПКА ======================
if st.button("🚀 Создать архив с контентом", type="primary"):
    if fields_filled:
        logo_img = get_processing_logo()
        if logo_img:
            with st.spinner("Обработка изображений..."):
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
                    st.session_state.file_name = f"LED_{tw}x{th}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                    st.success("✅ Архив создан!")
    else:
        st.warning("Заполните все параметры экрана")

# ====================== СКАЧИВАНИЕ ======================
if st.session_state.zip_data is not None:
    st.download_button(
        label="💾 Скачать ZIP-архив",
        data=st.session_state.zip_data,
        file_name=st.session_state.file_name,
        mime="application/zip",
        type="primary"
    )

st.caption("• Логотип по умолчанию: logo.png (можно заменить в сайдбаре)")
