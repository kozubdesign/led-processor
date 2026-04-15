import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="LED Processor", layout="wide") # wide для лучшего вида с превью

# Центрируем заголовок
st.markdown("<h1 style='text-align: center;'>🖼️ LED Content Processor</h1>", unsafe_allow_html=True)

# --- КОНСТАНТЫ ---
LOGO_PATH = "logo.png"
SOURCE_FOLDER = "images"

# --- ЛОГИКА ОБРАБОТКИ ОДНОГО КАДРА ДЛЯ ПРЕВЬЮ ---
def process_single_image(bg_path, logo_path, tw, th):
    try:
        if tw <= 0 or th <= 0: return None
        img = Image.open(bg_path).convert("RGB")
        logo = Image.open(logo_path).convert("RGBA")
        
        # 1. Фон
        ir, tr = img.width / img.height, tw / th
        nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - tw) / 2, (nh - th) / 2, (nw + tw) / 2, (nh + th) / 2))

        # 2. Лого (45% лимит)
        h_limit, w_limit = int(th * 0.45), int(tw * 0.45)
        lw_h = int(h_limit * (logo.width / logo.height))
        lh_w = int(w_limit * (logo.height / logo.width))
        lw, lh = (lw_h, h_limit) if lw_h <= w_limit else (w_limit, lh_w)
        
        l_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(l_res, ((tw - lw) // 2, (th - lh) // 2), l_res)
        return img
    except:
        return None

# --- ИНТЕРФЕЙС (Две колонки) ---
col1, col2 = st.columns([1.5, 1], gap="large")

with col2:
    st.subheader("⚙️ Параметры")
    w_mm = st.number_input("Ширина экрана (мм)", value=0, step=10)
    h_mm = st.number_input("Высота экрана (мм)", value=0, step=10)
    pitch = st.number_input("Шаг пикселя (мм)", value=0.0, format="%.2f", step=0.01)

    if w_mm > 0 and h_mm > 0 and pitch > 0:
        tw = int(round(w_mm / pitch))
        th = int(round(h_mm / pitch))
        st.info(f"Разрешение: **{tw}x{th} px**")
    else:
        tw, th = 0, 0
        st.warning("Введите параметры больше 0")

    # Кнопка скачивания
    process_btn = st.button("🚀 СГЕНЕРИРОВАТЬ ВЕСЬ АРХИВ", use_container_width=True)

with col1:
    st.subheader("👀 Предпросмотр (первый файл)")
    if os.path.exists(SOURCE_FOLDER) and os.listdir(SOURCE_FOLDER) and os.path.exists(LOGO_PATH):
        first_img = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))][0]
        full_path = os.path.join(SOURCE_FOLDER, first_img)
        
        if tw > 0 and th > 0:
            preview = process_single_image(full_path, LOGO_PATH, tw, th)
            if preview:
                st.image(preview, use_container_width=True, caption=f"Вид на экране {tw}x{th}")
        else:
            st.info("Здесь появится превью после ввода размеров")
    else:
        st.error("Ошибка: Проверьте наличие logo.png и папки images!")

# --- ЛОГИКА АРХИВА (ПРИ НАЖАТИИ КНОПКИ) ---
if process_btn:
    if tw <= 0 or th <= 0:
        st.error("Некорректные размеры!")
    else:
        with st.spinner('Сборка архива...'):
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            logo = Image.open(LOGO_PATH).convert("RGBA")
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for i, f_name in enumerate(bg_files):
                    img = process_single_image(os.path.join(SOURCE_FOLDER, f_name), LOGO_PATH, tw, th)
                    if img:
                        img_byte_arr = io.BytesIO()
                        img.save(img_byte_arr, format='JPEG', quality=95)
                        name = f"{tw}x{th}_{i+1}.jpg" if len(bg_files) > 1 else f"{tw}x{th}.jpg"
                        zip_file.writestr(name, img_byte_arr.getvalue())

            st.download_button(
                label="💾 СКАЧАТЬ ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"LED_{tw}x{th}_{datetime.now().strftime('%y%m%d')}.zip",
                mime="application/zip",
                use_container_width=True
            )
