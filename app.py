import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

# --- КОНСТАНТЫ ---
LOGO_PATH = "logo.png"
SOURCE_FOLDER = "images"

# 1. Настройка страницы
st.set_page_config(page_title="LED Processor", layout="centered")

# Ультимативный CSS для центровки и исправления отображения
st.markdown("""
    <style>
    /* 1. Общие отступы страницы */
    .block-container { 
        padding-top: 2rem !important; 
        padding-bottom: 2rem !important;
        max-width: 800px;
    }
    
    /* 2. Центровка заголовка */
    h1 { 
        text-align: center !important; 
        font-size: 2.2rem !important;
        line-height: 1.4 !important;
        margin-bottom: 1rem !important;
    }
    
    /* 3. Центровка всех текстов и меток */
    .stMarkdown, .stCaption, .stText, label, p {
        text-align: center !important;
        justify-content: center !important;
        display: flex !important;
        width: 100% !important;
    }
    
    /* 4. Центровка полей ввода */
    div[data-testid="stNumberInput"] {
        margin: 0 auto !important;
        width: 100% !important;
    }
    
    div[data-testid="stNumberInput"] > div {
        margin: 0 auto !important;
    }

    /* 5. Центровка и стиль зеленой кнопки */
    div.stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
    }

    div.stButton > button:first-child {
        background-color: #28a745 !important;
        color: white !important;
        height: 3.5rem !important;
        font-weight: bold !important;
        padding: 0 2rem !important;
        width: auto !important;
        min-width: 280px !important;
        border: none;
        margin-top: 1.5rem;
    }
    
    div.stButton > button:hover {
        background-color: #218838 !important;
        border: none;
    }

    /* 6. Центровка контейнера превью */
    [data-testid="stImage"] {
        display: flex !important;
        justify-content: center !important;
        margin: 0 auto !important;
    }

    /* Исправление для мобильных версий */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# --- ФУНКЦИЯ ОБРАБОТКИ ---
def process_single_image(bg_path, logo_path, tw, th):
    try:
        if not os.path.exists(bg_path) or not os.path.exists(logo_path):
            return None
            
        img = Image.open(bg_path).convert("RGB")
        logo = Image.open(logo_path).convert("RGBA")
        
        # Ресайз фона под целевое разрешение (Crop Fill)
        ir, tr = img.width / img.height, tw / th
        nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - tw) / 2, (nh - th) / 2, (nw + tw) / 2, (nh + th) / 2))

        # Наложение лого (центрированное, 45% от размера экрана)
        h_limit, w_limit = int(th * 0.45), int(tw * 0.45)
        lw_h = int(h_limit * (logo.width / logo.height))
        lh_w = int(w_limit * (logo.height / logo.width))
        lw, lh = (lw_h, h_limit) if lw_h <= w_limit else (w_limit, lh_w)
        
        l_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(l_res, ((tw - lw) // 2, (th - lh) // 2), l_res)
        return img
    except Exception as e:
        st.error(f"Ошибка при обработке {os.path.basename(bg_path)}: {e}")
        return None

# --- ИНТЕРФЕЙС ---

# Сначала превью
preview_placeholder = st.empty()

# Параметры (центрированная колонка)
_, central_col, _ = st.columns([0.5, 1, 0.5])

with central_col:
    st.write("")
    w_mm = st.number_input("Ширина экрана (мм)", value=0, step=10)
    h_mm = st.number_input("Высота экрана (мм)", value=0, step=10)
    pitch = st.number_input("Шаг пикселя (мм)", value=0.0, format="%.2f", step=0.01)

    fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0
    tw = int(round(w_mm / pitch)) if fields_filled else 0
    th = int(round(h_mm / pitch)) if fields_filled else 0

    if fields_filled:
        st.caption(f"Разрешение: {tw}x{th} px")
    
    st.write("")
    process_btn = st.button("Скачать архив с контентом")

# Отрисовка превью (800x300 max)
with preview_placeholder:
    if fields_filled:
        if os.path.exists(SOURCE_FOLDER) and os.path.exists(LOGO_PATH):
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if bg_files:
                img_preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), LOGO_PATH, tw, th)
                if img_preview:
                    scale = min(800 / tw, 300 / th, 1.0)
                    disp_w = int(tw * scale)
                    st.image(img_preview, width=disp_w)
            else:
                st.warning("В папке 'images' нет подходящих файлов.")
        else:
            st.error("Не найден logo.png или папка 'images'.")
    else:
        st.info("Введите параметры экрана")

# --- СБОРКА ZIP ---
if process_btn and fields_filled:
    with st.spinner('Подготовка контента...'):
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not bg_files:
            st.error("Нет изображений для обработки.")
        else:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for i, f_name in enumerate(bg_files):
                    res = process_single_image(os.path.join(SOURCE_FOLDER, f_name), LOGO_PATH, tw, th)
                    if res:
                        buf = io.BytesIO()
                        res.save(buf, format='JPEG', quality=95)
                        zip_file.writestr(f"{tw}x{th}_{i+1}.jpg", buf.getvalue())

            with central_col:
                st.download_button(
                    label="✅ СОХРАНИТЬ ZIP-АРХИВ",
                    data=zip_buffer.getvalue(),
                    file_name=f"LED_{tw}x{th}.zip",
                    mime="application/zip",
                    use_container_width=True
                )
