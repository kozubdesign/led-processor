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
            # 1. Создаем временный холст в правильных пропорциях (на основе мм)
            # Это нужно, чтобы логотип и фон не выглядели сплюснутыми при редактировании
            canvas_w, canvas_h = w_mm, h_mm
            # Масштабируем до разумных пределов для скорости (например, макс 2000px по стороне)
            limit = 2000
            scale_factor = min(limit/canvas_w, limit/canvas_h)
            temp_w, temp_h = int(canvas_w * scale_factor), int(canvas_h * scale_factor)
            
            img = ImageOps.fit(img.convert("RGB"), (temp_w, temp_h), Image.Resampling.LANCZOS)
            
            # 2. Накладываем логотип (пока всё в правильных пропорциях)
            lw, lh = active_logo.size
            max_scale = min(temp_w / lw, temp_h / lh)
            final_scale = max_scale * (user_scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
            
            img.paste(logo_res, ((temp_w - new_lw)//2, (temp_h - new_lh)//2), logo_res)
            
            # 3. ФИНАЛЬНЫЙ ШАГ: Анаморфное сжатие в реальное разрешение контроллера
            # Здесь игнорируются пропорции (resize без ImageOps.fit), чтобы попасть в сетку диодов
            final_img = img.resize((tw, th), Image.Resampling.LANCZOS)
            
            return final_img
    except: return None

# ====================== НАСТРОЙКА UI ======================
st.set_page_config(page_title="LED Generator Pro", layout="wide", page_icon="favicon.png")

# CSS стили оставляем без изменений (как в твоем исходнике)
logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")

st.markdown(f"""
    <style>
    .block-container {{ max-width: 800px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    .main-title {{ text-align: center; font-size: 1.6rem; font-weight: bold; margin-bottom: 20px; }}
    .res-box {{ 
        width: 100%; text-align: center; background-color: #d4edda; color: #155724; 
        padding: 15px; border-radius: 8px; margin: 10px 0; font-weight: bold; font-size: 1.2rem;
    }}
    .stButton > button, .stDownloadButton > button {{
        width: 320px !important; height: 54px !important; background-color: #28a745 !important;
        color: white !important; font-weight: 600 !important; border-radius: 8px !important;
    }}
    </style>
    <div class="logo-container" style="display: flex; justify-content: center; margin-bottom: 20px;">
        <img class="logo-img" style="width: 150px;" src="data:image/png;base64,{logo_black_base64}">
    </div>
    <div class='main-title'>Генератор контента (Асимметричный пиксель)</div>
    """, unsafe_allow_html=True)

# ====================== ЛОГИКА ВВОДА ======================
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

preview_placeholder = st.empty()
resolution_placeholder = st.empty()

logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = [os.path.join("images", f) for f in os.listdir("images") 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []

# Параметры экрана
col_dim, col_pitch = st.columns(2)
with col_dim:
    c1, c2 = st.columns(2)
    w_mm = c1.number_input("Ширина экрана (мм)", 0, value=8000)
    h_mm = c2.number_input("Высота экрана (мм)", 0, value=6000)

with col_pitch:
    c3, c4 = st.columns(2)
    pitch_x = c3.number_input("Шаг X (мм)", min_value=0.1, value=16.0, step=0.1)
    pitch_y = c4.number_input("Шаг Y (мм)", min_value=0.1, value=32.0, step=0.1)

tw, th = 0, 0
if w_mm > 0 and h_mm > 0:
    tw, th = int(round(w_mm / pitch_x)), int(round(h_mm / pitch_y))

logo_scale = st.slider("Размер лого (%)", 0, 100, 50)

# ====================== ПРЕВЬЮ И ГЕНЕРАЦИЯ ======================
if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    # Важно: передаем w_mm и h_mm для корректных пропорций внутри функции
    preview = get_processed_preview(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
    
    if preview:
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=85)
        img_str = base64.b64encode(buf.getvalue()).decode()
        preview_placeholder.markdown(f'''
            <div style="display: flex; flex-direction: column; align-items: center; margin-bottom: 10px;">
                <p style="color: gray; font-size: 0.8rem;">Вид файла для контроллера (сплюснут):</p>
                <img src="data:image/jpeg;base64,{img_str}" style="width: 100%; max-height: 400px; object-fit: contain; border: 1px solid #ddd;">
            </div>
        ''', unsafe_allow_html=True)
        resolution_placeholder.markdown(f"<div class='res-box'>Разрешение: {tw} × {th} px</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
btn_placeholder = st.empty()

if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    if st.session_state.zip_ready:
        zip_filename = f"{tw}x{th}_{datetime.now().strftime('%y_%m_%d')}.zip"
        btn_placeholder.download_button(label="Скачать архив", data=st.session_state.zip_ready, file_name=zip_filename, mime="application/zip")
    elif st.session_state.processing:
        btn_placeholder.button("⏳ Генерируем...", disabled=True)
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
