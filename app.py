import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps

# ====================== ФУНКЦИИ (С КЭШИРОВАНИЕМ) ======================
@st.cache_resource
def get_cached_logo(path):
    if os.path.exists(path):
        try: return Image.open(path).convert("RGBA")
        except: return None
    return None

@st.cache_data(show_spinner=False)
def get_processed_preview(bg_path, _logo_h, _logo_v, tw, th, user_scale_percent):
    """Кэшируем результат обработки для превью, чтобы оно не моргало"""
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
st.set_page_config(page_title="LED Processor", layout="wide")

st.markdown("""
    <style>
    .block-container { max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }
    [data-testid="stHeader"] { display: none; }
    .main-title { text-align: center; font-size: 1.8rem; font-weight: bold; margin-bottom: 10px; }
    div.stButton, div.stDownloadButton, div.element-container:has(button) {
        display: flex !important; justify-content: center !important; width: 100% !important;
    }
    .stButton > button, .stDownloadButton > button {
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important;
    }
    .res-box { 
        text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='main-title'>Создать контент для LED-экрана</div>", unsafe_allow_html=True)

# Состояние сессии
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

preview_placeholder = st.empty()
resolution_placeholder = st.empty()

logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = [os.path.join("images", f) for f in os.listdir("images") 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []

st.markdown("---")
c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
with c1: w_mm = st.number_input("Ширина (мм)", 0, value=0)
with c2: h_mm = st.number_input("Высота (мм)", 0, value=0)
with c3: pitch = st.number_input("Шаг (мм)", min_value=0.0, value=0.0, step=0.1, format="%g")

tw, th = 0, 0
if w_mm > 0 and h_mm > 0 and pitch > 0:
    tw, th = int(round(w_mm / pitch)), int(round(h_mm / pitch))

default_scale = 50 if tw >= th else 40
with c4: logo_scale = st.slider("Размер лого (%)", 0, 100, default_scale)

# ОТРИСОВКА ПРЕВЬЮ
if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    # Используем кэшированную версию функции
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
        btn_placeholder.download_button(
            label="📥 Скачать контент",
            data=st.session_state.zip_ready,
            file_name=f"led_{tw}x{th}.zip",
            mime="application/zip"
        )
    elif st.session_state.processing:
        btn_placeholder.button("⏳ Создание...", disabled=True)
        
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
        if btn_placeholder.button("Создать контент"):
            st.session_state.processing = True
            st.rerun()
