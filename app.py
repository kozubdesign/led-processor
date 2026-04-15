import streamlit as st
import zipfile
import io
import os
from PIL import Image
from datetime import datetime

# ====================== КОНСТАНТЫ ======================
LOGO_PATH = "logo.png"
SOURCE_FOLDER = "images"

# ====================== НАСТРОЙКА ======================
st.set_page_config(page_title="LED Processor", layout="wide")

# (CSS оставляем без изменений, он завязан на UI-требованиях)

@st.cache_data
def get_bg_files(folder):
    if not os.path.exists(folder): return []
    return [os.path.join(folder, f) for f in os.listdir(folder) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

@st.cache_resource
def get_cached_logo(path):
    if os.path.exists(path):
        try: return Image.open(path).convert("RGBA")
        except: return None
    return None

def process_single_image(bg_path, logo_rgba, tw, th, logo_percent):
    try:
        with Image.open(bg_path) as img:
            img = img.convert("RGB")
            # Ресайз и кроп фона
            ir, tr = img.width / img.height, tw / th
            nw, nh = (tw, int(tw / ir)) if ir < tr else (int(th * ir), th)
            
            img = img.resize((nw, nh), Image.Resampling.LANCZOS)
            img = img.crop(((nw - tw)//2, (nh - th)//2, (nw + tw)//2, (nh + th)//2))
            
            # Расчет размеров логотипа
            limit = int(min(tw, th) * (logo_percent / 100))
            lw, lh = logo_rgba.size
            scale = limit / max(lw, lh)
            new_size = (int(lw * scale), int(lh * scale))
            
            logo_res = logo_rgba.resize(new_size, Image.Resampling.LANCZOS)
            img.paste(logo_res, ((tw - new_size[0])//2, (th - new_size[1])//2), logo_res)
            return img
    except Exception as e:
        return None

# ====================== ИНИЦИАЛИЗАЦИЯ ======================
if 'zip_data' not in st.session_state:
    st.session_state.zip_data = None

logo_img = get_cached_logo(LOGO_PATH)
bg_files = get_bg_files(SOURCE_FOLDER)

# ====================== ВВОД ДАННЫХ ======================
col_w, col_h, col_p, col_s = st.columns([2, 2, 2, 3])
with col_w: w_mm = st.number_input("Ширина (мм)", 0, value=0, step=10)
with col_h: h_mm = st.number_input("Высота (мм)", 0, value=0, step=10)
with col_p: pitch = st.number_input("Шаг пикселя (мм)", 0, value=0, step=1)
with col_s: logo_percent = st.slider("Размер логотипа в %", 0, 150, 60, 5)

fields_filled = w_mm > 0 and h_mm > 0 and pitch > 0

# Сброс архива при изменении параметров
if fields_filled:
    params = f"{w_mm}_{h_mm}_{pitch}_{logo_percent}"
    if 'last_params' in st.session_state and st.session_state.last_params != params:
        st.session_state.zip_data = None
    st.session_state.last_params = params

# ====================== ПРЕВЬЮ И ЛОГИКА ======================
if fields_filled and logo_img and bg_files:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))
    
    # Превью (генерируем один раз для интерфейса)
    preview = process_single_image(bg_files[0], logo_img, tw, th, logo_percent)
    if preview:
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=90) # 100 quality избыточно для превью
        st.image(buf, use_column_width=False, width=600)
    
    st.success(f"**Разрешение: {tw} × {th} px**")

    if st.session_state.zip_data is None:
        if st.button("Генерировать контент"):
            with st.spinner("Обработка..."):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, path in enumerate(bg_files):
                        res = process_single_image(path, logo_img, tw, th, logo_percent)
                        if res:
                            b = io.BytesIO()
                            res.save(b, format="JPEG", quality=95, subsampling=0)
                            zf.writestr(f"{tw}x{th}_{i+1:02d}.jpg", b.getvalue())
                
                st.session_state.zip_data = zip_buffer.getvalue()
                st.rerun()
    else:
        st.download_button(
            label="Скачать архив",
            data=st.session_state.zip_data,
            file_name=f"LED_{datetime.now().strftime('%y%m%d')}.zip",
            mime="application/zip"
        )
