import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

st.set_page_config(page_title="LED Processor (Static)", layout="centered")

st.title("🖼️ LED Content Processor")
st.write("Настройте параметры экрана для предустановленного контента.")

# --- КОНСТАНТЫ ПУТЕЙ ---
LOGO_PATH = "logo.png"
SOURCE_FOLDER = "images"

# --- БОКОВАЯ ПАНЕЛЬ ---
st.sidebar.header("Параметры экрана")
w_mm = st.sidebar.number_input("Ширина экрана (мм)", value=1000)
h_mm = st.sidebar.number_input("Высота экрана (мм)", value=500)
pitch = st.sidebar.number_input("Шаг пикселя (мм)", value=3.91, format="%.2f")

tw = int(round(w_mm / pitch))
th = int(round(h_mm / pitch))

st.sidebar.info(f"Итоговое разрешение: **{tw}x{th} px**")

# --- ЛОГИКА ОБРАБОТКИ ---
if st.button("СГЕНЕРИРОВАТЬ И СКАЧАТЬ АРХИВ"):
    # Проверка наличия лого и папки
    if not os.path.exists(LOGO_PATH):
        st.error("Критическая ошибка: файл logo.png не найден в репозитории!")
    elif not os.path.exists(SOURCE_FOLDER) or not os.listdir(SOURCE_FOLDER):
        st.error("Критическая ошибка: папка 'images' пуста или не существует!")
    else:
        with st.spinner('Подготовка контента...'):
            logo = Image.open(LOGO_PATH).convert("RGBA")
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                for i, f_name in enumerate(bg_files):
                    img = Image.open(os.path.join(SOURCE_FOLDER, f_name)).convert("RGB")
                    
                    # 1. Подготовка фона
                    ir, tr = img.width / img.height, tw / th
                    nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
                    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
                    img = img.crop(((nw - tw) / 2, (nh - th) / 2, (nw + tw) / 2, (nh + th) / 2))

                    # 2. Размер лого (лимит 45%)
                    h_limit, w_limit = int(th * 0.45), int(tw * 0.45)
                    lw_h = int(h_limit * (logo.width / logo.height))
                    lh_w = int(w_limit * (logo.height / logo.width))
                    
                    lw, lh = (lw_h, h_limit) if lw_h <= w_limit else (w_limit, lh_w)
                    l_res = logo.resize((lw, lh), Image.Resampling.LANCZOS)

                    # 3. Наложение
                    img.paste(l_res, ((tw - lw) // 2, (th - lh) // 2), l_res)
                    
                    # Сохранение в архив
                    out_name = f"{tw}x{th}_{i+1}.jpg" if len(bg_files) > 1 else f"{tw}x{th}.jpg"
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=95)
                    zip_file.writestr(out_name, img_byte_arr.getvalue())

            date_str = datetime.now().strftime("%y %m %d")
            zip_filename = f"Контент {tw}x{th} + {date_str}.zip"
            
            st.success(f"Готово! Обработано изображений: {len(bg_files)}")
            st.download_button(
                label="💾 СКАЧАТЬ ГОТОВЫЙ АРХИВ",
                data=zip_buffer.getvalue(),
                file_name=zip_filename,
                mime="application/zip"
            )
