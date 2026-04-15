import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps
from datetime import datetime

# ====================== ФУНКЦИИ ======================
@st.cache_resource
def get_cached_logo(path):
    if os.path.exists(path):
        try: return Image.open(path).convert("RGBA")
        except: return None
    return None

def get_base64_img(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        except: return ""
    return ""

@st.cache_data(show_spinner=False)
def get_processed_preview(bg_path, _logo_h, _logo_v, tw, th, user_scale_percent, w_mm, h_mm):
    return process_single_image(bg_path, _logo_h, _logo_v, tw, th, user_scale_percent, w_mm, h_mm)

def process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent, w_mm, h_mm):
    try:
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo: return None
        
        with Image.open(bg_path) as img:
            # Сначала делаем холст в реальных пропорциях экрана (мм)
            # чтобы логотип не исказился при наложении
            temp_aspect = w_mm / h_mm
            temp_h = 1000  # Базовая высота для рендеринга
            temp_w = int(temp_h * temp_aspect)
            
            img = ImageOps.fit(img.convert("RGB"), (temp_w, temp_h), Image.Resampling.LANCZOS)
            
            lw, lh = active_logo.size
            max_scale = min(temp_w / lw, temp_h / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
            
            img.paste(logo_res, ((temp_w - new_lw)//2, (temp_h - new_lh)//2), logo_res)
            
            # ФИНАЛЬНОЕ СЖАТИЕ: превращаем мм в пиксели (вот тут картинка сплющится)
            return img.resize((tw, th), Image.Resampling.LANCZOS)
    except: return None

# ====================== UI ======================
st.set_page_config(page_title="LED Generator", layout="wide")

logo_black_base64 = get_base64_img("logo_black.png")
st.markdown(f"""
    <style>
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; }}
    .res-box {{ text-align: center; background-color: #d4edda; padding: 15px; border-radius: 8px; font-weight: bold; }}
    </style>
    <div style="text-align: center; margin-bottom: 20px;">
        <img width="150" src="data:image/png;base64,{logo_black_base64}">
        <h2>Генератор контента</h2>
    </div>
    """, unsafe_allow_html=True)

# Ввод данных (сбросил на 0 по умолчанию)
c1, c2 = st.columns(2)
with c1:
    w_mm = st.number_input("Ширина экрана (мм)", 0, value=0)
    h_mm = st.number_input("Высота экрана (мм)", 0, value=0)
with c2:
    pitch_x = st.number_input("Шаг пикселя X (мм)", 0.0, value=0.0, step=0.1)
    pitch_y = st.number_input("Шаг пикселя Y (мм)", 0.0, value=0.0, step=0.1)

tw, th = 0, 0
if w_mm > 0 and h_mm > 0 and pitch_x > 0 and pitch_y > 0:
    tw, th = int(round(w_mm / pitch_x)), int(round(h_mm / pitch_y))

logo_scale = st.slider("Размер лого (%)", 0, 100, 50)

# ====================== РЕЗУЛЬТАТ ======================
logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = [os.path.join("images", f) for f in os.listdir("images") 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []

if tw > 0 and bg_files:
    preview = get_processed_preview(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
    if preview:
        st.image(preview, caption=f"Превью файла ({tw}x{th} px)", use_container_width=True)
        st.markdown(f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)

        if st.button("Создать контент"):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_f:
                for f in bg_files:
                    res = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
                    if res:
                        img_io = io.BytesIO()
                        res.save(img_io, format='JPEG', quality=95)
                        zip_f.writestr(os.path.basename(f), img_io.getvalue())
            
            st.download_button("Скачать ZIP", zip_buffer.getvalue(), f"{tw}x{th}.zip")
