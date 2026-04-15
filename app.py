import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

# --- КОНСТАНТЫ ---
DEFAULT_LOGO_PATH = "logo.png"
BLACK_LOGO_PATH = "logo_black.png"
FAVICON_PATH = "favicon.ico"
FAVICON_PNG = "favicon.png"
SOURCE_FOLDER = "images"

# --- ОПРЕДЕЛЕНИЕ ЛОГОТИПА ДЛЯ ШАПКИ ---
def get_header_logo():
    is_dark = st.get_option("theme.base") == "dark"
    if is_dark and os.path.exists(BLACK_LOGO_PATH):
        return BLACK_LOGO_PATH
    elif os.path.exists(DEFAULT_LOGO_PATH):
        return DEFAULT_LOGO_PATH
    return None

# --- НАСТРОЙКА СТРАНИЦЫ ---
if os.path.exists(FAVICON_PATH):
    st.set_page_config(page_title="LED Processor", page_icon=FAVICON_PATH, layout="centered")
elif os.path.exists(FAVICON_PNG):
    st.set_page_config(page_title="LED Processor", page_icon=FAVICON_PNG, layout="centered")
else:
    st.set_page_config(page_title="LED Processor", layout="centered")

# --- CSS для максимальной центровки ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        max-width: 800px !important;
        margin: 0 auto !important;
    }
    
    h1 {
        text-align: center !important;
        font-size: 2.25rem !important;
        margin-bottom: 0.8rem !important;
    }
    
    .header-logo {
        display: block;
        margin: 0 auto 1rem auto !important;
        height: 50px;
        object-fit: contain;
    }
    
    .preview-info {
        text-align: center !important;
        color: #666;
        font-size: 1.05rem;
        margin-bottom: 1.8rem !important;
    }
    
    /* Центрируем все поля ввода */
    div[data-testid="stNumberInput"] {
        margin: 0 auto !important;
        max-width: 320px !important;
    }
    
    /* Узкое поле для шага пикселя */
    .narrow-input {
        max-width: 200px !important;
        margin: 0 auto !important;
    }
    
    /* Кнопка по центру */
    .stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }
    .stButton > button {
        height: 3.5rem !important;
        font-weight: bold !important;
        font-size: 1.08rem !important;
        background-color: #28a745 !important;
        color: white !important;
        min-width: 320px !important;
        width: auto !important;
        margin-top: 1.2rem !important;
    }
    
    [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        margin: 1.8rem auto !important;
    }
    
    .success-box {
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ЛОГОТИП В ШАПКЕ ---
header_logo = get_header_logo()
if header_logo:
    st.image(header_logo, use_container_width=False, width=220, clamp=True)

st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)
st.markdown('<p class="preview-info">Введите параметры экрана, чтобы увидеть превью</p>', unsafe_allow_html=True)

# --- SESSION STATE ---
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None
    st.session_state.file_name = None

if 'uploaded_logo' not in st.session_state:
    st.session_state.uploaded_logo = None

# --- ЛОГОТИП ДЛЯ ОБРАБОТКИ ---
def get_logo_image():
    if st.session_state.uploaded_logo is not None:
        return Image.open(st.session_state.uploaded_logo).convert("RGBA")
    if os.path.exists(DEFAULT_LOGO_PATH):
        try:
            return Image.open(DEFAULT_LOGO_PATH).convert("RGBA")
        except:
            return None
    return None

# --- ОБРАБОТКА ИЗОБРАЖЕНИЯ ---
def process_single_image(bg_path, logo_img, target_w, target_h, logo_percent=45):
    try:
        if not os.path.exists(bg_path) or logo_img is None:
            return None
            
        img = Image.open(bg_path).convert("RGB")
        
        ir = img.width / img.height
        tr = target_w / target_h
        if ir < tr:
            nw, nh = target_w, int(target_w / ir)
        else:
            nh, nw = target_h, int(target_h * ir)
        
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - target_w)//2, (nh - target_h)//2, 
                       (nw + target_w)//2, (nh + target_h)//2))
        
        limit = int(min(target_w, target_h) * (logo_percent / 100))
        lw = int(limit * (logo_img.width / logo_img.height))
        lh = int(limit * (logo_img.height / logo_img.width))
        
        if lw > limit:
            lw = limit
            lh = int(lw * (logo_img.height / logo_img.width))
        else:
            lh = limit
            lw = int(lh * (logo_img.width / logo_img.height))
        
        logo_resized = logo_img.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(logo_resized, ((target_w - lw) // 2, (target_h - lh) // 2), logo_resized)
        return img
        
    except Exception as e:
        st.error(f"Ошибка: {e}")
        return None

# --- САЙДБАР ---
with st.sidebar:
    st.header("Настройки")
    st.session_state.uploaded_logo = st.file_uploader("Загрузить другой логотип", 
                                                     type=['png', 'jpg', 'jpeg'])
    
    if st.session_state.uploaded_logo:
        st.success("✓ Логотип загружен")
    elif os.path.exists(DEFAULT_LOGO_PATH):
        st.info("Используется logo.png")
    
    logo_percent = st.slider("Размер логотипа (%)", 20, 70, 45, 5)

# --- ПАРАМЕТРЫ ЭКРАНА (всё по центру) ---
st.markdown("### Параметры экрана")

col1, col2 = st.columns([1, 1])
with col1:
    w_mm = st.number_input("Ширина экрана (мм)", 
                          min_value=0, max_value=9999999, value=0, step=10)
with col2:
    h_mm = st.number_input("Высота экрана (мм)", 
                          min_value=0, max_value=9999999, value=0, step=10)

# Узкое поле шага пикселя по центру
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
else:
    tw = th = 0

# --- ПРЕВЬЮ ---
if fields_filled:
    logo_img = get_logo_image()
    if logo_img:
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if bg_files:
            preview_img = process_single_image(
                os.path.join(SOURCE_FOLDER, bg_files[0]), logo_img, tw, th, logo_percent
            )
            if preview_img:
                scale = min(800 / tw, 400 / th, 1.0)
                display_w = int(tw * scale)
                st.image(preview_img, width=display_w, caption=f"Превью — {bg_files[0]}")
        else:
            st.warning("В папке **images** нет изображений")
    else:
        st.error("Логотип не найден")

# --- КНОПКА СОЗДАНИЯ ---
if st.button("🚀 Создать архив с контентом", type="primary"):
    if fields_filled:
        logo_img = get_logo_image()
        if logo_img and os.path.exists(SOURCE_FOLDER):
            with st.spinner("Обработка изображений..."):
                bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if bg_files:
                    zip_buffer = io.BytesIO()
                    processed = 0
                    progress = st.progress(0)
                    
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        for i, fname in enumerate(bg_files):
                            res = process_single_image(
                                os.path.join(SOURCE_FOLDER, fname), logo_img, tw, th, logo_percent
                            )
                            if res:
                                buf = io.BytesIO()
                                res.save(buf, format="JPEG", quality=95, optimize=True)
                                zf.writestr(f"{tw}x{th}_{i+1:02d}.jpg", buf.getvalue())
                                processed += 1
                            progress.progress((i + 1) / len(bg_files))
                    
                    zip_buffer.seek(0)
                    st.session_state.zip_data = zip_buffer.getvalue()
                    st.session_state.file_name = f"LED_{tw}x{th}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                    
                    st.success(f"✅ Готово! Обработано {processed} изображений.")
    else:
        st.warning("Заполните все параметры экрана")

# --- КНОПКА СКАЧИВАНИЯ ---
if st.session_state.zip_data is not None:
    st.download_button(
        label="💾 Скачать ZIP-архив",
        data=st.session_state.zip_data,
        file_name=st.session_state.file_name,
        mime="application/zip",
        type="primary"
    )
    
    if st.button("Очистить результат"):
        st.session_state.zip_data = None
        st.rerun()

st.caption("• Логотип по умолчанию: logo.png (можно заменить в сайдбаре)")
