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
        try:
            return Image.open(path).convert("RGBA")
        except:
            return None
    return None

@st.cache_data
def get_image_list(folder):
    if not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
        return []
    return [os.path.join(folder, f) for f in os.listdir(folder) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

def get_base64_img(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        except:
            return ""
    return ""

def process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent):
    # Защита от некорректных размеров
    if tw <= 0 or th <= 0:
        return None
    try:
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo:
            return None
        
        with Image.open(bg_path) as img:
            # Приведение фона к нужному разрешению
            img = ImageOps.fit(img.convert("RGB"), (tw, th), Image.Resampling.LANCZOS)
            
            lw, lh = active_logo.size
            # Расчет масштаба, чтобы лого не вылезало за границы
            max_scale = min(tw / lw, th / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            
            new_lw = max(1, int(lw * final_scale))
            new_lh = max(1, int(lh * final_scale))
            
            logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
            
            # Центрирование
            ox = (tw - new_lw) // 2
            oy = (th - new_lh) // 2
            
            img.paste(logo_res, (ox, oy), logo_res)
            return img
    except Exception as e:
        return None

# ====================== НАСТРОЙКА UI ======================
st.set_page_config(page_title="LED Generator", page_icon="favicon.png", layout="wide")

# Загрузка ресурсов
logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")
logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = get_image_list("images")

st.markdown(f"""
    <style>
    .stApp {{ background-color: #f5f7f9; }}
    @media (prefers-color-scheme: dark) {{ .stApp {{ background-color: #0e1117; }} }}
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    .logo-container {{ display: flex; justify-content: center; margin: 20px 0; }}
    .logo-img {{ width: 150px; }}
    .main-title {{ text-align: center; font-size: 1.6rem; font-weight: bold; margin-bottom: 20px; }}
    div.stButton, div.stDownloadButton {{ display: flex !important; justify-content: center !important; width: 100% !important; }}
    .stButton > button, .stDownloadButton > button {{
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important; border: none !important;
    }}
    .res-box {{ 
        text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
        border: 1px solid #c3e6cb;
    }}
    </style>
    
    <div class="logo-container">
        <img class="logo-img" src="data:image/png;base64,{logo_black_base64 if logo_black_base64 else logo_h_base64}">
    </div>
    <div class='main-title'>Генератор контента</div>
    """, unsafe_allow_html=True)

# ====================== ЛОГИКА СОСТОЯНИЯ ======================
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

preview_placeholder = st.empty()
resolution_placeholder = st.empty()

# БЛОК ВВОДА
c1, c2, c3 = st.columns(3)
with c1: w_mm = st.number_input("Ширина (мм)", min_value=0, value=0)
with c2: h_mm = st.number_input("Высота (мм)", min_value=0, value=0)
with c3: pitch = st.number_input("Шаг (мм)", min_value=0.0, value=0.0, step=0.1, format="%g")

tw, th = 0, 0
if w_mm > 0 and h_mm > 0 and pitch > 0:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))

logo_scale = st.slider("Размер лого (%)", 5, 100, 50 if tw >= th else 40)

# ПРЕВЬЮ
if tw > 0 and th > 0 and bg_files:
    preview = process_single_image(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale)
    if preview:
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=85)
        img_str = base64.b64encode(buf.getvalue()).decode()
        
        preview_placeholder.markdown(f'''
            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 400px; border-radius: 8px; border: 1px solid #ddd;">
            </div>
        ''', unsafe_allow_html=True)
        resolution_placeholder.markdown(f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)
elif not bg_files:
    st.info("Добавьте изображения в папку 'images'")

st.markdown("<br>", unsafe_allow_html=True)

# КНОПКИ УПРАВЛЕНИЯ
if tw > 0 and th > 0 and (logo_h_img or logo_v_img) and bg_files:
    if st.session_state.zip_ready:
        current_date = datetime.now().strftime("%y_%m_%d")
        st.download_button(
            label="💾 СКАЧАТЬ АРХИВ", 
            data=st.session_state.zip_ready, 
            file_name=f"{tw}x{th}_{current_date}.zip", 
            mime="application/zip"
        )
        if st.button("Сбросить и создать новый"):
            st.session_state.zip_ready = None
            st.rerun()
            
    elif st.session_state.processing:
        with st.spinner("Генерация набора изображений..."):
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for f in bg_files:
                    proc = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale)
                    if proc:
                        img_byte_arr = io.BytesIO()
                        proc.save(img_byte_arr, format='JPEG', quality=95)
                        zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
            
            st.session_state.zip_ready = zip_buffer.getvalue()
            st.session_state.processing = False
            st.rerun()
    else:
        if st.button("ГЕНЕРИРОВАТЬ"):
            st.session_state.processing = True
            st.rerun()
