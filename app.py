import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

# --- КОНСТАНТЫ ---
SOURCE_FOLDER = "images"
DEFAULT_LOGO = "logo.png"

# --- НАСТРОЙКА СТРАНИЦЫ ---
st.set_page_config(page_title="LED Processor", layout="centered", page_icon="🖼️")

# Улучшенный CSS
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
        border: none !important;
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
    
    .center-text {
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# --- ИНИЦИАЛИЗАЦИЯ SESSION STATE ---
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None
    st.session_state.file_name = None
    st.session_state.resolution = None

# --- ФУНКЦИЯ ОБРАБОТКИ ИЗОБРАЖЕНИЯ ---
def process_single_image(bg_path, logo_image, target_width, target_height, logo_percent=45):
    try:
        if not os.path.exists(bg_path):
            return None
            
        img = Image.open(bg_path).convert("RGB")
        logo = logo_image.convert("RGBA")
        
        # Crop-Fill: приводим фон к нужному разрешению
        ir = img.width / img.height
        tr = target_width / target_height
        
        if ir < tr:
            nw = target_width
            nh = int(target_width / ir)
        else:
            nh = target_height
            nw = int(target_height * ir)
            
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - target_width) // 2, (nh - target_height) // 2,
                       (nw + target_width) // 2, (nh + target_height) // 2))
        
        # Наложение логотипа
        limit = int(min(target_width, target_height) * (logo_percent / 100))
        lw = int(limit * (logo.width / logo.height))
        lh = int(limit * (logo.height / logo.width))
        
        if lw > limit:
            lw = limit
            lh = int(lw * (logo.height / logo.width))
        else:
            lh = limit
            lw = int(lh * (logo.width / logo.height))
        
        l_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        
        paste_x = (target_width - lw) // 2
        paste_y = (target_height - lh) // 2
        
        img.paste(l_res, (paste_x, paste_y), l_res)
        return img
        
    except Exception as e:
        st.error(f"Ошибка обработки {os.path.basename(bg_path)}: {e}")
        return None

# --- БОКОВАЯ ПАНЕЛЬ НАСТРОЕК ---
with st.sidebar:
    st.header("Настройки")
    
    # Загрузка логотипа
    uploaded_logo = st.file_uploader("Загрузить логотип", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_logo:
        logo_image = Image.open(uploaded_logo)
        st.success("Логотип загружен")
    elif os.path.exists(DEFAULT_LOGO):
        logo_image = Image.open(DEFAULT_LOGO)
        st.info("Используется logo.png из папки")
    else:
        st.error("Логотип не найден. Загрузите свой.")
        logo_image = None
    
    logo_percent = st.slider("Размер логотипа (%)", min_value=20, max_value=70, value=45, step=5)
    
    jpeg_quality = st.slider("Качество JPEG", min_value=70, max_value=100, value=95, step=5)

# --- ОСНОВНОЙ ИНТЕРФЕЙС ---
_, central_col, _ = st.columns([0.4, 1.2, 0.4])

with central_col:
    st.markdown("### Параметры экрана")
    
    col1, col2 = st.columns(2)
    with col1:
        w_mm = st.number_input("Ширина экрана (мм)", min_value=0, value=0, step=10)
    with col2:
        h_mm = st.number_input("Высота экрана (мм)", min_value=0, value=0, step=10)
    
    pitch = st.number_input("Шаг пикселя (мм)", min_value=0.0, value=0.0, format="%.2f", step=0.01)
    
    fields_filled = w_mm > 0 and h_mm > 0 and pitch >= 0.01
    
    if fields_filled:
        tw = int(round(w_mm / pitch))
        th = int(round(h_mm / pitch))
        st.success(f"**Разрешение экрана: {tw} × {th} пикселей**")
    else:
        tw = th = 0
        st.info("Введите ширину, высоту и шаг пикселя")

# --- ПРЕВЬЮ ---
preview_placeholder = st.empty()

with preview_placeholder:
    if fields_filled and logo_image:
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if bg_files:
            preview_img = process_single_image(
                os.path.join(SOURCE_FOLDER, bg_files[0]), 
                logo_image, tw, th, logo_percent
            )
            if preview_img:
                # Масштабируем превью для удобного отображения
                scale = min(800 / tw, 420 / th, 1.0)
                disp_w = int(tw * scale)
                st.image(preview_img, width=disp_w, caption="Превью (первый файл)")
        else:
            st.warning("В папке 'images' нет изображений")
    elif fields_filled:
        st.info("Загрузите логотип в боковой панели")

# --- ОБРАБОТКА И СОЗДАНИЕ ZIP ---
if st.button("🚀 Создать и скачать архив", type="primary", use_container_width=True) and fields_filled and logo_image:
    with st.spinner("Обработка изображений..."):
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if not bg_files:
            st.error("Нет изображений в папке 'images'")
        else:
            zip_buffer = io.BytesIO()
            processed_count = 0
            
            progress_bar = st.progress(0)
            
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for i, f_name in enumerate(bg_files):
                    res = process_single_image(
                        os.path.join(SOURCE_FOLDER, f_name), 
                        logo_image, tw, th, logo_percent
                    )
                    
                    if res:
                        buf = io.BytesIO()
                        res.save(buf, format='JPEG', quality=jpeg_quality, optimize=True)
                        zip_file.writestr(f"{tw}x{th}_{i+1:02d}.jpg", buf.getvalue())
                        processed_count += 1
                    
                    progress_bar.progress((i + 1) / len(bg_files))
            
            # Сохраняем в session_state
            zip_buffer.seek(0)
            st.session_state.zip_data = zip_buffer.getvalue()
            st.session_state.file_name = f"LED_Content_{tw}x{th}_{datetime.now().strftime('%Y%m%d_%H%M')}.zip"
            st.session_state.resolution = f"{tw}x{th}"
            
            st.success(f"✅ Готово! Обработано {processed_count} изображений")

# --- КНОПКА СКАЧИВАНИЯ ---
if st.session_state.zip_data is not None:
    with central_col:
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

# Финальная информация
st.caption("Приложение автоматически центрирует логотип и приводит фон к разрешению экрана методом Crop-Fill")
