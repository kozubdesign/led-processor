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
if os.path.exists(LOGO_PATH):
    fav_logo = Image.open(LOGO_PATH)
    st.set_page_config(page_title="LED Processor", page_icon=fav_logo, layout="wide")
else:
    st.set_page_config(page_title="LED Processor", layout="wide")

# 2. Выровненный заголовок с логотипом
if os.path.exists(LOGO_PATH):
    # Используем HTML/CSS для идеального выравнивания по центру высоты
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: center; gap: 20px; margin-bottom: 20px;">
            <img src="data:image/png;base64,{st.image_to_base64 if hasattr(st, 'image_to_base64') else ''}" 
            width="80" style="vertical-align: middle;"> </div>
        """, unsafe_allow_html=True
    )
    # Альтернативный чистый способ Streamlit для выравнивания
    col_l, col_r = st.columns([1, 4])
    with col_l:
        st.write("") # Отступ сверху для компенсации
        st.image(LOGO_PATH, width=80)
    with col_r:
        st.markdown("<h1 style='margin-left: -100px;'>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)
else:
    st.markdown("<h1 style='text-align: center;'>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# --- ЛОГИКА ОБРАБОТКИ ---
def process_single_image(bg_path, logo_path, tw, th):
    try:
        if tw <= 0 or th <= 0: return None
        img = Image.open(bg_path).convert("RGB")
        logo = Image.open(logo_path).convert("RGBA")
        
        ir, tr = img.width / img.height, tw / th
        nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
        img = img.resize((nw, nh), Image.Resampling.LANCZOS)
        img = img.crop(((nw - tw) / 2, (nh - th) / 2, (nw + tw) / 2, (nh + th) / 2))

        h_limit, w_limit = int(th * 0.45), int(tw * 0.45)
        lw_h = int(h_limit * (logo.width / logo.height))
        lh_w = int(w_limit * (logo.height / logo.width))
        lw, lh = (lw_h, h_limit) if lw_h <= w_limit else (w_limit, lh_w)
        
        l_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)
        img.paste(l_res, ((tw - lw) // 2, (th - lh) // 2), l_res)
        return img
    except:
        return None

# --- ИНТЕРФЕЙС ---
st.divider()
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
        st.warning("Введите параметры")

    process_btn = st.button("🚀 Создать архив", use_container_width=True)

with col1:
    st.subheader("👀 Предпросмотр")
    if os.path.exists(SOURCE_FOLDER) and os.listdir(SOURCE_FOLDER) and os.path.exists(LOGO_PATH):
        files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if files:
            full_path = os.path.join(SOURCE_FOLDER, files[0])
            if tw > 0 and th > 0:
                preview = process_single_image(full_path, LOGO_PATH, tw, th)
                if preview:
                    # Масштаб 1:3 для превью
                    st.image(preview, width=(tw // 3 if tw // 3 > 200 else 300), 
                             caption=f"Масштаб 1:3 (Итог: {tw}x{th} px)")
            else:
                st.info("Введите размеры для превью")
    else:
        st.error("Файлы не найдены")

# --- СБОРКА ZIP ---
if process_btn and tw > 0 and th > 0:
    with st.spinner('Подготовка...'):
        bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
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
