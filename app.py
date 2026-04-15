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
def get_processed_preview(bg_path, _logo_h, _logo_v, tw, th, user_scale_percent):
    return process_single_image(bg_path, _logo_h, _logo_v, tw, th, user_scale_percent)

def process_single_image(bg_path, logo_h, logo_v, tw, th, user_scale_percent):
    try:
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo: return None
        with Image.open(bg_path) as img:
            img = ImageOps.fit(img.convert("RGB"), (tw, th), Image.Resampling.LANCZOS)
            lw, lh = active_logo.size
            max_scale = min(tw / lw, th / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
            img.paste(logo_res, ((tw - new_lw)//2, (th - new_lh)//2), logo_res)
            return img
    except: return None

# ====================== НАСТРОЙКА UI ======================
st.set_page_config(page_title="LED Generator", layout="wide")

logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")

st.markdown(f"""
    <style>
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    
    /* Убираем подсказки "Press Enter to apply" */
    [data-testid="stInputInstructions"] {{
        display: none !important;
    }}

    /* --- ИЗМЕНЕНИЯ ЦВЕТА СЛАЙДЕРА --- */
    
    /* Полоса слева от ползунка (активная зона) */
    div[data-baseweb="slider"] > div > div > div:nth-child(1) {{
        background: #28a745 !important;
    }}
    
    /* Сам ползунок (круг) */
    div[data-baseweb="slider"] > div > div > div > div {{
        background-color: #28a745 !important;
    }}

    /* Цвет цифр над ползунком */
    div[data-testid="stThumbValue"] {{
        color: black !important;
        font-weight: bold;
    }}
    
    /* ------------------------------- */

    .logo-container {{
        display: flex;
        justify-content: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }}
    
    .logo-img {{ width: 150px; }}
    
    @media (prefers-color-scheme: light) {{
        .logo-dark {{ display: none; }}
        .logo-light {{ display: block; }}
    }}
    @media (prefers-color-scheme: dark) {{
        .logo-light {{ display: none; }}
        .logo-dark {{ display: block; }}
    }}
    
    @media (max-width: 640px) {{
        .logo-img {{ width: 100px; }}
    }}

    .main-title {{ text-align: center; font-size: 1.6rem; font-weight: bold; margin-bottom: 20px; }}
    .stNumberInput, .stSlider {{ width: 100% !important; }}
    [data-testid="column"] {{ padding-left: 0rem !important; padding-right: 0rem !important; }}

    div.stButton, div.stDownloadButton, div.element-container:has(button) {{
        display: flex !important; justify-content: center !important; width: 100% !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important;
    }}
    .res-box {{ 
        text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
    }}
    </style>
    
    <div class="logo-container">
        <img class="logo-img logo-light" src="data:image/png;base64,{logo_black_base64}">
        <img class="logo-img logo-dark" src="data:image/png;base64,{logo_h_base64}">
    </div>
    <div class='main-title'>LED Content Generator</div>
    """, unsafe_allow_html=True)

# ====================== ЛОГИКА ======================
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

preview_placeholder = st.empty()
resolution_placeholder = st.empty()

logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = [os.path.join("images", f) for f in os.listdir("images") 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []

c1, c2, c3 = st.columns(3)
with c1: w_mm = st.number_input("Ширина (мм)", 0, value=0)
with c2: h_mm = st.number_input("Высота (мм)", 0, value=0)
with c3: pitch = st.number_input("Шаг (мм)", min_value=0.0, value=0.0, step=0.1, format="%g")

tw, th = 0, 0
if w_mm > 0 and h_mm > 0 and pitch > 0:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))

cs = st.columns(1)[0]
default_scale = 50 if tw >= th else 40
with cs:
    logo_scale = st.slider("Размер лого (%)", 0, 100, default_scale)

if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    preview = get_processed_preview(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale)
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

st.markdown("<br>", unsafe_allow_html=True)
btn_placeholder = st.empty()

if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    if st.session_state.zip_ready:
        current_date = datetime.now().strftime("%y_%m_%d")
        zip_filename = f"{tw}x{th}_{current_date}.zip"
        btn_placeholder.download_button(label="Скачать", data=st.session_state.zip_ready, file_name=zip_filename, mime="application/zip")
    elif st.session_state.processing:
        btn_placeholder.button("⏳ Генерируем...", disabled=True)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for f in bg_files:
                processed = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale)
                if processed:
                    img_byte_arr = io.BytesIO()
                    processed.save(img_byte_arr, format='JPEG', quality=95)
                    zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
        st.session_state.zip_ready = zip_buffer.getvalue()
        st.session_state.processing = False
        st.rerun()
    else:
        if btn_placeholder.button("Генерировать"):
            st.session_state.processing = True
            st.rerun()
