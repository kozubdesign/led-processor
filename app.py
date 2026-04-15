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

#SVG Иконка Спиннера (белая) в Base64
spinner_svg_base64 = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA1MTIgNTEyIj48cGF0aCBmaWxsPSJ3aGl0ZSIgZD0iTTI4OCA5NkMyODggNjQuNjkgMzEzLjQgMzguNjIgMzQ0IDM4LjYyQzM3NC42IDM4LjYyIDQwMCA2NC42OSA0MDAgOTZDMDAgMTI3LjMgMzc0LjYgMTUzLjQgMzQ0IDE1My40QzMxMy40IDE1My40IDI4OCAxMjcuMyAyODggOTZ6TTQ4MCAyNTZDMzgwIDM4MC4zIDMxNi42IDQ4MCAyNTYgNDgwQzE5NS40IDQ4MCAxMzIgMzgwLjMgMTMyIDI1NkMxMzIgMTMxLjcgMTk1LjQgOTYgMjU2IDk2QzMxNi42IDk2IDQ4MCAxMzEuNyA0ODAgMjU2ek0yNTYgMTI4QzE5NS40IDEyOCAxMzIgMTk1LjQgMTMyIDI1NkMxMzIgMzE2LjYgMTk1LjQgNDgwIDI1NiA0ODBDMzE2LjYgNDgwIDQ4MCAzMTYuNiA0ODAgMjU2QzQ4MCAxOTUuNCAzMTYuNiAxMjggMjU2IDEyOHpNMTEyIDk2QzExMiAxMjcuMyA4Ny4zOCAxNTMuNCA1Ni43NSAxNTMuNEMyNi4xMyAxNTMuNCAxLjUgMTI3LjMgMS41IDk2QzEuNSA2NC42OSAyNi4xMyAzOC42MiA1Ni43NSAzOC42MkMxMTIgMzguNjIgMTEyIDY0LjY5IDExMiA5NnpNMjU2IDQxNkMyMjQuNiA0MTYgMTk4LjYgNDQxLjQgMTk4LjYgNDcyQzE5OC42IDUwMi42IDIyNC42IDUyOCAyNTYgNTI4QzI4Ny40IDUyOCAzMTMuNCA1MDIuNiAzMTMuNCA0NzJDMzEzLjQgNDQxLjQgMjg3LjQgNDE2IDI1NiA0MTZ6TTQ0OCA0MTZDMTE2LjYgNDE2IDM5MC42IDQ0MS40IDM5MC42IDQ3MkMzOTAuNiA1MDIuNiA0MTYuNiA1MjggNDQ4IDUyOEM0NzkuNCA1MjggNTA1LjQgNTAyLjYgNTA1LjQgNDcyQzUwNS40IDQ0MS40IDQ3OS40IDQxNiA0NDggNDE2ek01Ni43NSA0MTZDMjYuMTMgNDE2IDEuNSA0NDEuNCAxLjUgNDcyQzEuNSA1MDIuNiAyNi4xMyA1MjggNTYuNzUgNTI4Qzg3LjM4IDUyOCA4Ny4zOCA1MDIuNiA4Ny4zOCA0NzJDODcuMzggNDQxLjQgODcuMzggNDE2IDU2Ljc1IDQxNnpNNDE2IDk2QzQxNiAxMjcuMyAzOTAuNiAxNTMuNCAzNjAgMTUzLjRDMzI5LjQgMTUzLjQgMzA0IDEyNy4zIDMwNCA5NkMzMDQgNjQuNjkgMzI5LjQgMzguNjIgMzYwLDM4LjYyQzQxNiAzOC42MiA0MTYgNjQuNjkgNDE2IDk2ek0xMTIgMjU2QzExMiAyODcuNCA4Ny4zOCAzMTMuNCA1Ni43NSAzMTMuNEMyNi4xMyAzMTMuNCAxLjUgMjg3LjQgMS41IDI1NkMxLjUgMjI0LjYgMjYuMTMgMTk4LjYgNTYuNzUgMTk4LjZDMTEyIDE5OC42IDExMiAyMjQuNiAxMTIgMjU2ek01MDcuNSA5NkM1MDcuNSAxMjcuMyA0ODIuOSAxNTMuNCA0NTIuMyAxNTMuNEM0MjEuNiAxNTMuNCAzOTcgMTI3LjMgMzk3IDk2QzM5NyA2NC42OSA0MjEuNiAzOC42MiA0NTIuMyAzOC42MkM0ODIuOSAzOC42MiA1MDcuNSA2NC42OSA1MDcuNSA5NnpNNDQ4IDMzNkM0NDggMzY3LjQgNDE2LjYgMzkzLjQgMzg2IDM5My40QzM1NS40IDM5My40IDMyOS40IDM2Ny40IDMyOS40IDMzNkMzMjkuNCAzMDQuNiAzNTUuNCAyNzguNiAzODYgMjc4LjZDMzgwIDI3OC42IDM4MCAzMDQuNiA0NDggMzM2ek00NTIuMyAyNTZDMzgzLjUgMjU2IDMyOC45IDI4Ny40IDMyOC45IDMxOC4zQzMyOC45IDM0OS4xIDM4My41IDM4MC41IDQ1Mi4zIDM4MC41QzUxMiAzODAuNSA1MTEuNSAzNDkuMSA1MTEuNSAzMTguM0M1MTEuNSAyODcuNCA1MTIgMjU2IDQ1Mi4zIDI1NnpNMTEyIDMzNkMxMTIgMzY3LjQgODcuMzggMzkzLjQgNTYuNzUgMzkzLjRDMjYuMTMgMzkzLjQgMS41IDM2Ny40IDEuNSAzMzZDMS41IDMwNC42IDI2LjEzIDI3OC42IDU2Ljc1IDI3OC42Qzg3LjM4IDI3OC42IDg3LjM4IDMwNC42IDExMiAzMzZ6Ii8+PC9zdmc+"

st.markdown(f"""
    <style>
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    [data-testid="stInputInstructions"] {{ display: none !important; }}
    
    .logo-container {{
        display: flex;
        justify-content: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }}
    
    .logo-img {{ width: 150px; }}
    
    /* Анимация вращения */
    @keyframes spin {{
        from {{ transform: rotate(0deg); }}
        to {{ transform: rotate(360deg); }}
    }}

    /* Заменяем эмодзи на SVG-спиннер (через Base64) для заблокированной кнопки */
    button[disabled] p::before {{
        content: "";
        display: inline-block;
        width: 20px;
        height: 20px;
        margin-right: 12px;
        background-image: url("{spinner_svg_base64}");
        background-size: contain;
        background-repeat: no-repeat;
        vertical-align: middle;
        animation: spin 1.5s linear infinite; /* Чуть быстрее и плавнее */
    }}

    @media (prefers-color-scheme: light) {{
        .logo-dark {{ display: none; }}
        .logo-light {{ display: block; }}
    }}
    @media (prefers-color-scheme: dark) {{
        .logo-light {{ display: none; }}
        .logo-dark {{ display: block; }}
    }}
    
    .main-title {{ text-align: center; font-size: 1.6rem; font-weight: bold; margin-bottom: 20px; }}
    
    div.stButton, div.stDownloadButton, div.element-container:has(button) {{
        display: flex !important; justify-content: center !important; width: 100% !important;
    }}
    .stButton > button, .stDownloadButton > button {{
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important;
    }}
    .res-box {{ 
        width: 100%; box-sizing: border-box;
        text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
    }}
    </style>
    
    <div class="logo-container">
        <img class="logo-img logo-light" src="data:image/png;base64,{logo_black_base64}">
        <img class="logo-img logo-dark" src="data:image/png;base64,{logo_h_base64}">
    </div>
    <div class='main-title'>Генератор контента</div>
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
with c3: pitch_str = st.text_input("Шаг (мм)", value="0")

tw, th = 0, 0
pitch_x, pitch_y = 0.0, 0.0
is_asymmetric = "/" in pitch_str

try:
    if is_asymmetric:
        parts = pitch_str.split("/")
        pitch_x = float(parts[0].replace(",", "."))
        pitch_y = float(parts[1].replace(",", "."))
    else:
        pitch_x = pitch_y = float(pitch_str.replace(",", "."))
except:
    pass

if w_mm > 0 and h_mm > 0 and pitch_x > 0 and pitch_y > 0:
    tw, th = int(round(w_mm / pitch_x)), int(round(h_mm / pitch_y))

cs = st.columns(1)[0]
default_scale = 50 if tw >= th else 40
with cs:
    logo_scale = st.slider("Размер лого (%)", 0, 100, default_scale)

if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    preview = get_processed_preview(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
    if preview:
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=85)
        img_str = base64.b64encode(buf.getvalue()).decode()
        preview_placeholder.markdown(f'''
            <div style="display: flex; justify-content: center; margin-bottom: 10px;">
                <img src="data:image/jpeg;base64,{img_str}" style="max-width: 100%; max-height: 400px; border-radius: 8px; border: 1px solid #ddd;">
            </div>
        ''', unsafe_allow_html=True)
        
        res_label = "Разрешение медиафасада" if is_asymmetric else "Разрешение экрана"
        resolution_placeholder.markdown(f"<div class='res-box'>{res_label}: {tw} × {th} px</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
btn_placeholder = st.empty()

if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    if st.session_state.zip_ready:
        current_date = datetime.now().strftime("%y_%m_%d")
        zip_filename = f"{tw}x{th}_{current_date}.zip"
        btn_placeholder.download_button(label="Скачать", data=st.session_state.zip_ready, file_name=zip_filename, mime="application/zip")
    elif st.session_state.processing:
        # Текст остается, иконка подставляется CSS-ом
        btn_placeholder.button("Идет генерация...", disabled=True)
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
        if btn_placeholder.button("Создать контент"):
            st.session_state.processing = True
            st.rerun()
