import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

# --- КОНСТАНТЫ ---
DEFAULT_LOGO_PATH = "logo.png"
FAVICON_PATH = "favicon.ico"
FAVICON_PNG = "favicon.png"
SOURCE_FOLDER = "images"

# --- НАСТРОЙКА СТРАНИЦЫ ---
if os.path.exists(FAVICON_PATH):
    st.set_page_config(page_title="LED Processor", page_icon=FAVICON_PATH, layout="centered")
elif os.path.exists(FAVICON_PNG):
    st.set_page_config(page_title="LED Processor", page_icon=FAVICON_PNG, layout="centered")
else:
    st.set_page_config(page_title="LED Processor", layout="centered")

# --- CSS ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 820px !important;
    }
    h1 {
        text-align: center !important;
        font-size: 2.3rem !important;
        margin-bottom: 1.5rem !important;
    }
    .stButton > button {
        height: 3.6rem !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        background-color: #28a745 !important;
        color: white !important;
        width: 100% !important;
        margin-top: 1rem;
    }
    .stButton > button:hover {
        background-color: #218838 !important;
    }
    [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        margin: 1.5rem auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None
    st.session_state.file_name = None
    st.session_state.resolution = None

if 'logo_image' not in st.session_state:
    st.session_state.logo_image = None

# --- ЗАГРУЗКА ЛОГОТИПА (с приоритетом загруженного) ---
def get_logo_image():
    uploaded = st.session_state.get('uploaded_logo')
    if uploaded is not None:
        return Image.open(uploaded).convert("RGBA")
    
    if os.path.exists(DEFAULT_LOGO_PATH):
        try:
            return Image.open(DEFAULT_LOGO_PATH).convert("RGBA")
        except:
            st.warning("Не удалось открыть logo.png")
            return None
    return None

# --- ФУНКЦИЯ ОБРАБОТКИ ---
def process_single_image(bg_path, logo_img, target_w, target_h, logo_percent=45):
    try:
        if not os.path.exists(bg_path) or logo_img is None:
            return None
            
        img = Image.open(bg_path).convert("RGB")
        
        # Crop-Fill
        ir = img.width / img.height
        tr = target_w / target_h
        if ir < tr:
            nw, nh = target_w, int(target_w / ir)
        else:
            nh, nw = target_h, int(target_h * ir)
        
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - target_w)//2, (nh - target_h)//2, 
                       (nw + target_w)//2, (nh + target_h)//2))
        
        # Наложение логотипа
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
        
        paste_x = (target_w - lw) // 2
        paste_y = (target_h - lh) // 2
        
        img.paste(logo_resized, (paste_x, paste_y), logo_resized)
        return img
        
    except Exception as e:
        st.error(f"Ошибка обработки изображения: {e}")
        return None

# --- САЙДБАР ---
with st.sidebar:
    st.header("Настройки")
    
    # Загрузка логотипа
    uploaded_logo = st.file_uploader("Загрузить другой логотип", 
                                    type=['png', 'jpg', 'jpeg'],
                                    key="uploaded_logo")
    
    if uploaded_logo:
        st.success("✓ Логотип загружен и используется")
    elif os.path.exists(DEFAULT_LOGO_PATH):
        st.info("Используется logo.png из папки")
    else:
        st.error("Файл logo.png не найден!")
    
    # Размер логотипа
    logo_percent = st.slider("Размер логотипа (%) от экрана", 
                            min_value=20, max_value=70, 
                            value=45, step=5)

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
_, col, _ = st.columns([0.4, 1.2, 0.4])
with col:
    st.markdown("### Параметры экрана")
    
    c1, c2 = st.columns(2)
    with c1:
        w_mm = st.number_input("Ширина экрана (мм)", min_value=0, value=0, step=10)
    with c2:
        h_mm = st.number_input("Высота экрана (мм)", min_value=0, value=0, step=10)
    
    pitch = st.number_input("Шаг пикселя (мм)", min_value=0.0, value=0.0, format="%.2f", step=0.01)
    
    fields_filled = w_mm > 0 and h_mm > 0 and pitch >= 0.01
    
    if fields_filled:
        tw = int(round(w_mm / pitch))
        th = int(round(h_mm / pitch))
        st.success(f"**Разрешение: {tw} × {th} px**")
    else:
        tw = th = 0

# --- ПРЕВЬЮ (ограничено 800×500) ---
preview_placeholder = st.empty()

with preview_placeholder:
    if fields_filled:
        logo_img = get_logo_image()
        if logo_img:
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            if bg_files:
                preview = process_single_image(
                    os.path.join(SOURCE_FOLDER, bg_files[0]), 
                    logo_img, tw, th, logo_percent
                )
                if preview:
                    # Ограничение размера превью
                    scale = min(800 / tw, 500 / th, 1.0)
                    display_width = int(tw * scale)
                    st.image(preview, width=display_width, 
                            caption=f"Превью — {bg_files[0]}")
            else:
                st.warning("В папке **images** нет изображений")
        else:
            st.error("Логотип не загружен")
    else:
        st.info("Введите параметры экрана, чтобы увидеть превью")

# --- ОБРАБОТКА И ZIP ---
if st.button("🚀 Создать архив с контентом", type="primary", use_container_width=True) and fields_filled:
    logo_img = get_logo_image()
    if not logo_img:
        st.error("Не удалось загрузить логотип")
    else:
        with st.spinner("Обработка изображений..."):
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) 
                       if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            if not bg_files:
                st.error("Нет изображений в папке images")
            else:
                zip_buffer = io.BytesIO()
                processed = 0
                progress_bar = st.progress(0)
                
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, fname in enumerate(bg_files):
                        result = process_single_image(
                            os.path.join(SOURCE_FOLDER, fname), 
                            logo_img, tw, th, logo_percent
                        )
                        if result:
                            buf = io.BytesIO()
                            result.save(buf, format="JPEG", quality=95, optimize=True)
                            zf.writestr(f"{tw}x{th}_{i+1:02d}.jpg", buf.getvalue())
                            processed += 1
                        
                        progress_bar.progress((i+1) / len(bg_files))
                
                zip_buffer.seek(0)
                st.session_state.zip_data = zip_buffer.getvalue()
                st.session_state.file_name = f"LED_{tw}x{th}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                
                st.success(f"✅ Готово! Обработано {processed} изображений.")

# --- СКАЧИВАНИЕ ---
if st.session_state.zip_data is not None:
    with col:
        st.download_button(
            label="💾 Скачать ZIP-архив",
            data=st.session_state.zip_data,
            file_name=st.session_state.file_name,
            mime="application/zip",
            use_container_width=True,
            type="primary"
        )
        
        if st.button("Очистить результат"):
            st.session_state.zip_data = None
            st.session_state.file_name = None
            st.rerun()

st.caption("Логотип по умолчанию: logo.png • Можно заменить через загрузчик в сайдбаре")
