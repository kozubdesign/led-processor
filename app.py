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

# Ультра-компактный отступ сверху и стили
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    h1 { margin-top: -1rem !important; text-align: center; font-size: 2.2rem !important; }
    /* Стиль для полей ввода, чтобы они были крупнее */
    .stNumberInput input { font-size: 1.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# --- ФУНКЦИЯ ОБРАБОТКИ ---
def process_single_image(bg_path, logo_path, tw, th):
    try:
        img = Image.open(bg_path).convert("RGB")
        logo = Image.open(logo_path).convert("RGBA")
        
        ir, tr = img.width / img.height, tw / th
        nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - tw) / 2, (nh - th) / 2, (nw + tw) / 2, (nh + th) / 2))

        # Наложение лого (45% от размера)
        h_limit, w_limit = int(th * 0.45), int(tw * 0.45)
        lw_h = int(h_limit * (logo.width / logo.height))
        lh_w = int(w_limit * (logo.height / logo.width))
        lw, lh = (lw_h, h_limit) if lw_h <= w_limit else (w_limit, lh_w)
        
        l_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(l_res, ((tw - lw) // 2, (th - lh) // 2), l_res)
        return img
    except Exception as e:
        return None

# --- ИНТЕРФЕЙС ---

# Место для превью
preview_placeholder = st.empty()

# Параметры (Увеличенная ширина col_mid для удобства)
_, col_mid, _ = st.columns([0.3, 2, 0.3])

with col_mid:
    st.write("")
    w_mm = st.number_input("Ширина экрана (мм)", value=0, step=10)
    h_mm = st.number_input("Высота экрана (мм)", value=0, step=10)
    pitch = st.number_input("Шаг пикселя (мм)", value=0.0, format="%.2f", step=0.01)

    fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0
    tw = int(round(w_mm / pitch)) if fields_filled else 0
    th = int(round(h_mm / pitch)) if fields_filled else 0

    if fields_filled:
        st.caption(f"Итоговое разрешение: {tw}x{th} px")
        # Зеленая кнопка
        st.markdown("""
            <style>
            div.stButton > button:first-child {
                background-color: #28a745 !important;
                color: white !important;
                height: 3rem !important;
                font-weight: bold !important;
            }
            </style>""", unsafe_allow_html=True)
    
    process_btn = st.button("Скачать архив с контентом", use_container_width=True)

# Логика отрисовки превью
with preview_placeholder:
    if fields_filled:
        if os.path.exists(SOURCE_FOLDER) and os.path.exists(LOGO_PATH):
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if bg_files:
                img_preview = process_single_image(os.path.join(SOURCE_FOLDER, bg_files[0]), LOGO_PATH, tw, th)
                if img_preview:
                    # РАСЧЕТ МАСШТАБА ДЛЯ ВПИСЫВАНИЯ В 800x300
                    scale_w = 800 / tw
                    scale_h = 300 / th
                    final_scale = min(scale_w, scale_h, 1.0)
                    
                    disp_w = int(tw * final_scale)
                    
                    # Центрируем картинку через колонки
                    c1, c2, c3 = st.columns([1, 10, 1])
                    c2.image(img_preview, width=disp_w)
            else:
                st.warning("Папка 'images' пуста")
        else:
            st.error("Отсутствует 'logo.png' или папка 'images'")
    else:
        # Заглушка, пока нет размеров
        st.info("Укажите размеры экрана для генерации превью")

# --- СБОРКА ZIP ---
if process_btn and fields_filled:
    with st.spinner('Подготовка файлов...'):
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, f_name in enumerate(bg_files):
                processed = process_single_image(os.path.join(SOURCE_FOLDER, f_name), LOGO_PATH, tw, th)
                if processed:
                    buf = io.BytesIO()
                    processed.save(buf, format='JPEG', quality=95)
                    zip_file.writestr(f"{tw}x{th}_{i+1}.jpg", buf.getvalue())

        with col_mid:
            st.download_button(
                label="✅ СОХРАНИТЬ ZIP-АРХИВ",
                data=zip_buffer.getvalue(),
                file_name=f"LED_Content_{tw}x{th}.zip",
                mime="application/zip",
                use_container_width=True
            )
