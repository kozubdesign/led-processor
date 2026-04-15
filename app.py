import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="LED Content Processor", layout="centered")

st.title("🖼️ LED Content Processor")
st.write("Загрузите контент, настройте параметры и скачайте готовый архив.")

# --- БОКОВАЯ ПАНЕЛЬ (НАСТРОЙКИ) ---
st.sidebar.header("Параметры экрана")
w_mm = st.sidebar.number_input("Ширина экрана (мм)", value=1000)
h_mm = st.sidebar.number_input("Высота экрана (мм)", value=500)
pitch = st.sidebar.number_input("Шаг пикселя (мм)", value=3.91, format="%.2f")

tw = int(round(w_mm / pitch))
th = int(round(h_mm / pitch))

st.sidebar.info(f"Итоговое разрешение: **{tw}x{th} px**")

# --- ЗАГРУЗКА ФАЙЛОВ ---
logo_file = st.file_uploader("Загрузите ЛОГОТИП (PNG/JPG)", type=["png", "jpg", "jpeg"])
bg_files = st.file_uploader("Загрузите ИСХОДНИКИ (один или несколько)", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

if st.button("ОБРАБОТАТЬ И СКАЧАТЬ"):
    if not logo_file or not bg_files:
        st.error("Ошибка: загрузите логотип и хотя бы один исходник!")
    else:
        # Подготовка логотипа
        logo = Image.open(logo_file).convert("RGBA")
        
        # Буфер для ZIP-архива в памяти
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, bg_file in enumerate(bg_files):
                img = Image.open(bg_file).convert("RGB")
                
                # 1. Подготовка фона (Fill & Crop)
                ir, tr = img.width / img.height, tw / th
                nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
                img = img.resize((nw, nh), Image.Resampling.LANCZOS)
                img = img.crop(((nw - tw) / 2, (nh - th) / 2, (nw + tw) / 2, (nh + th) / 2))

                # 2. Расчет размера лого (лимит 45% по длинной стороне)
                h_limit, w_limit = int(th * 0.45), int(tw * 0.45)
                lw_h = int(h_limit * (logo.width / logo.height))
                lh_w = int(w_limit * (logo.height / logo.width))
                
                lw, lh = (lw_h, h_limit) if lw_h <= w_limit else (w_limit, lh_w)
                l_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)

                # 3. Наложение
                img.paste(l_res, ((tw - lw) // 2, (th - lh) // 2), l_res)
                
                # Сохранение в байты
                img_name = f"{tw}x{th}_{i+1}.jpg" if len(bg_files) > 1 else f"{tw}x{th}.jpg"
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG', quality=95)
                
                # Добавление в архив
                zip_file.writestr(img_name, img_byte_arr.getvalue())

        # Формирование кнопки скачивания
        date_str = datetime.now().strftime("%y %m %d")
        zip_filename = f"Контент {tw}x{th} + {date_str}.zip"
        
        st.success(f"Готово! Обработано файлов: {len(bg_files)}")
        st.download_button(
            label="💾 СКАЧАТЬ АРХИВ",
            data=zip_buffer.getvalue(),
            file_name=zip_filename,
            mime="application/zip"
        )