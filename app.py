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

def reset_zip():
    st.session_state.zip_ready = None

@st.cache_data(show_spinner=False)
def get_processed_preview(bg_path, _logo_h, _logo_v, tw, th, user_scale_percent, w_mm, h_mm):
    try:
        active_logo = _logo_h if tw >= th else _logo_v
        if not active_logo: return None
        with Image.open(bg_path) as img:
            img.draft("RGB", (tw, th)) 
            temp_aspect = w_mm / h_mm
            temp_h = 1000 
            temp_w = int(temp_h * temp_aspect)
            img = ImageOps.fit(img.convert("RGB"), (temp_w, temp_h), Image.Resampling.BILINEAR)
            lw, lh = active_logo.size
            max_scale = min(temp_w / lw, temp_h / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.BILINEAR)
            img.paste(logo_res, ((temp_w - new_lw)//2, (temp_h - new_lh)//2), logo_res)
            return img.resize((tw, th), Image.Resampling.BILINEAR)
    except: return None

def process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent, w_mm, h_mm):
    try:
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo: return None
        with Image.open(bg_path) as img:
            temp_aspect = w_mm / h_mm
            temp_h = 1200
            temp_w = int(temp_h * temp_aspect)
            img = ImageOps.fit(img.convert("RGB"), (temp_w, temp_h), Image.Resampling.LANCZOS)
            lw, lh = active_logo.size
            max_scale = min(temp_w / lw, temp_h / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
            img.paste(logo_res, ((temp_w - new_lw)//2, (temp_h - new_lh)//2), logo_res)
            return img.resize((tw, th), Image.Resampling.LANCZOS)
    except: return None

# ====================== НАСТРОЙКА UI ======================
st.set_page_config(page_title="LEDsi Генератор контента", layout="wide", page_icon="favicon.png")

logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")

st.markdown(f"""
    <style>
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    .logo-container {{ display: flex; justify-content: center; margin-top: 20px; margin-bottom: 20px; }}
    .logo-img {{ width: 150px; }}
    
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    
    /* Контрастная иконка загрузки (темная с зеленым акцентом) */
    button[disabled] div[data-testid="stMarkdownContainer"] p::before {{
        content: ""; 
        display: inline-block; 
        width: 18px; 
        height: 18px; 
        margin-right: 10px;
        vertical-align: middle; 
        border-radius: 50%;
        border: 2px solid rgba(0,0,0,0.1); /* Светло-серое кольцо */
        border-top-color: #28a745;       /* Зеленая активная часть */
        animation: spin 0.8s linear infinite;
    }}
    
    @media (prefers-color-scheme: light) {{ .logo-dark {{ display: none; }} .logo-light {{ block; }} }}
    @media (prefers-color-scheme: dark) {{ .logo-light {{ display: none; }} .logo-dark {{ block; }} }}
    .main-title {{ text-align: center; font-size: 1.6rem; font-weight: bold; margin-bottom: 20px; }}
    
    div.stButton, div.stDownloadButton, div.element-container:has(button) {{
        display: flex !important; justify-content: center !important; width: 100% !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        width: 320px !important; height: 54px !important; font-weight: 600 !important; border-radius: 8px !important;
    }}
    
    .res-box {{ 
        width: 100%; text-align: center; background-color: #d4edda; color: #155724; 
        padding: 10px; border-radius: 8px; margin: 15px 0; 
        font-weight: 500; font-size: 1.0rem;
    }}
    </style>
    <div class="logo-container">
        <img class="logo-img logo-light" src="data:image/png;base64,{logo_black_base64}">
        <img class="logo-img logo-dark" src="data:image/png;base64,{logo_h_base64}">
    </div>
    <div class='main-title'>Генератор контента</div>
    """, unsafe_allow_html=True)

if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

preview_placeholder = st.empty()
resolution_placeholder = st.empty()

logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = [os.path.join("images", f) for f in os.listdir("images") 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []

c1, c2, c3 = st.columns(3)
with c1: w_mm = st.number_input("Ширина (мм)", 0, value=0, on_change=reset_zip)
with c2: h_mm = st.number_input("Высота (мм)", 0, value=0, on_change=reset_zip)
with c3: pitch_str = st.text_input("Шаг (мм)", value="0", on_change=reset_zip)

tw, th = 0, 0
pitch_x, pitch_y = 0.0, 0.0
is_asymmetric = "/" in pitch_str
try:
    if is_asymmetric:
        parts = pitch_str.split("/")
        pitch_x, pitch_y = float(parts[0].replace(",", ".")), float(parts[1].replace(",", "."))
    else:
        pitch_x = pitch_y = float(pitch_str.replace(",", "."))
except: pass

if w_mm > 0 and h_mm > 0 and pitch_x > 0 and pitch_y > 0:
    tw, th = int(round(w_mm / pitch_x)), int(round(h_mm / pitch_y))

cs = st.columns(1)[0]
default_scale = 50 if tw >= th else 40
with cs: logo_scale = st.slider("Размер лого (%)", 0, 100, default_scale, on_change=reset_zip)

if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    preview = get_processed_preview(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
    if preview:
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=75)
        img_str = base64.b64encode(buf.getvalue()).decode()
        preview_placeholder.markdown(f'''
            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 300px; border-radius: 8px; border: 1px solid #ddd;">
            </div>
        ''', unsafe_allow_html=True)
        res_label = "Разрешение медиафасада" if is_asymmetric else "Разрешение экрана"
        resolution_placeholder.markdown(f"<div class='res-box'>{res_label}: {tw} × {th} px</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# БЛОК КНОПОК
if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    if st.session_state.zip_ready:
        current_date = datetime.now().strftime("%y_%m_%d")
        zip_filename = f"{tw}x{th}_{current_date}.zip"
        st.download_button(label="Скачать", data=st.session_state.zip_ready, file_name=zip_filename, mime="application/zip", type="primary")
    
    elif st.session_state.processing:
        st.button("Идет генерация...", disabled=True)
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for f in bg_files:
                processed = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
                if processed:
                    img_byte_arr = io.BytesIO()
                    processed.save(img_byte_arr, format='JPEG', quality=95)
                    zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
        
        st.session_state.zip_ready = zip_buffer.getvalue()
        st.session_state.processing = False
        st.rerun()
    
    else:
        if st.button("Создать контент", type="primary"):
            st.session_state.processing = True
            st.rerun()
