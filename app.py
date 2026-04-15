import streamlit as st
import zipfile
import io
import os
from PIL import Image, ImageOps
from datetime import datetime

# ====================== ФУНКЦИИ ======================
@st.cache_resource
def load_logo(path):
    return Image.open(path).convert("RGBA") if os.path.exists(path) else None

@st.cache_data(show_spinner=False)
def process_image(bg_path, logo_h, logo_v, tw, th, scale):
    active = logo_h if tw >= th else logo_v
    if not active: return None
    try:
        with Image.open(bg_path) as img:
            img = ImageOps.fit(img.convert("RGB"), (tw, th), Image.Resampling.LANCZOS)
            lw, lh = active.size
            new_size = int(min(tw/lw, th/lh) * scale / 100)
            logo = active.resize((new_size, new_size), Image.Resampling.LANCZOS) if lw == lh else \
                   active.resize((int(lw*new_size/lw), int(lh*new_size/lh)), Image.Resampling.LANCZOS)
            img.paste(logo, ((tw - logo.width)//2, (th - logo.height)//2), logo)
            return img
    except:
        return None

# ====================== НАСТРОЙКА ======================
st.set_page_config(page_title="LED Generator", layout="wide", page_icon="favicon.png")

st.markdown("""
    <style>
    .block-container {max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important;}
    [data-testid="stHeader"] {display: none;}
    .main-title {text-align: center; font-size: 1.6rem; font-weight: bold; margin: 20px 0;}
    .stButton > button, .stDownloadButton > button {
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important;
    }
    .res-box {text-align: center; background: #d4edda; color: #155724; padding: 15px; 
              border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;}
    </style>
    <div class='main-title'>Генератор контента</div>
""", unsafe_allow_html=True)

# ====================== ЛОГИКА ======================
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

preview = st.empty()
res_text = st.empty()

logo_h = load_logo("logo_h.png")
logo_v = load_logo("logo_v.png")

bg_files = [os.path.join("images", f) for f in os.listdir("images")
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []

c1, c2, c3 = st.columns(3)
with c1: w = st.number_input("Ширина (мм)", value=0)
with c2: h = st.number_input("Высота (мм)", value=0)
with c3: p = st.number_input("Шаг (мм)", value=0.0, step=0.1, format="%g")

tw = th = 0
if w and h and p:
    tw, th = int(round(w/p)), int(round(h/p))

scale = st.slider("Размер лого (%)", 0, 100, 50 if tw >= th else 40)

if tw and bg_files and (logo_h or logo_v):
    img = process_image(bg_files[0], logo_h, logo_v, tw, th, scale)
    if img:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=85)
        preview.image(buf.getvalue(), use_column_width=True)
        res_text.markdown(f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)

btn = st.empty()

if tw and bg_files and (logo_h or logo_v):
    if st.session_state.zip_ready:
        date = datetime.now().strftime("%y_%m_%d")
        btn.download_button("Скачать", st.session_state.zip_ready, f"{tw}x{th}_{date}.zip", "application/zip")
    elif st.session_state.processing:
        btn.button("⏳ Генерируем...", disabled=True)
    elif btn.button("Создать контент"):
        st.session_state.processing = True
        st.rerun()

# Обработка ZIP
if st.session_state.processing:
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as z:
        for f in bg_files:
            img = process_image(f, logo_h, logo_v, tw, th, scale)
            if img:
                b = io.BytesIO()
                img.save(b, "JPEG", quality=95)
                z.writestr(os.path.basename(f), b.getvalue())
    st.session_state.zip_ready = zip_buf.getvalue()
    st.session_state.processing = False
    st.rerun()
