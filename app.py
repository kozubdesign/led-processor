import streamlit as st
import zipfile
import io
import os
import base64
import numpy as np
from PIL import Image, ImageOps
from datetime import datetime, timedelta
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip

# ====================== ФУНКЦИИ ОБРАБОТКИ ======================
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
    st.session_state.video_zip_ready = None
    st.session_state.processing = False
    st.session_state.video_processing = False

def process_images_logic(bg_files, logo_h, logo_v, tw, th, scale, w_mm, h_mm):
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        progress_bar = st.progress(0)
        for i, f in enumerate(bg_files):
            # Вызов вашей функции обработки из старого кода
            active_logo = logo_h if tw >= th else logo_v
            with Image.open(f) as img:
                temp_aspect = w_mm / h_mm
                temp_h = 1200
                temp_w = int(temp_h * temp_aspect)
                img = ImageOps.fit(img.convert("RGB"), (temp_w, temp_h), Image.Resampling.LANCZOS)
                lw, lh = active_logo.size
                max_scale = min(temp_w / lw, temp_h / lh)
                final_scale = max_scale * (scale / 100)
                new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
                logo_res = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
                img.paste(logo_res, ((temp_w - new_lw)//2, (temp_h - new_lh)//2), logo_res)
                final_img = img.resize((tw, th), Image.Resampling.LANCZOS)
                
                img_io = io.BytesIO()
                final_img.save(img_io, format='JPEG', quality=95)
                zf.writestr(os.path.basename(f), img_io.getvalue())
            progress_bar.progress((i + 1) / len(bg_files))
    return zip_buf.getvalue()

def process_videos_logic(video_files, logo_h, logo_v, tw, th, scale):
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        progress_bar = st.progress(0)
        for i, f in enumerate(video_files):
            st.write(f"Обработка: {os.path.basename(f)}...")
            try:
                clip = VideoFileClip(f)
                target_ratio = tw / th
                clip_ratio = clip.w / clip.h
                if clip_ratio > target_ratio:
                    new_w = int(clip.h * target_ratio)
                    clip = clip.crop(x_center=clip.w/2, width=new_w)
                else:
                    new_h = int(clip.w / target_ratio)
                    clip = clip.crop(y_center=clip.h/2, height=new_h)
                clip = clip.resize(width=tw, height=th)
                
                active_logo_pil = logo_h if tw >= th else logo_v
                lw, lh = active_logo_pil.size
                max_scale = min(tw / lw, th / lh)
                final_scale = max_scale * (scale / 100)
                new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
                logo_res = active_logo_pil.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
                
                logo_clip = (ImageClip(np.array(logo_res))
                             .set_duration(clip.duration)
                             .set_position(("center", "center")))
                
                final_video = CompositeVideoClip([clip, logo_clip])
                temp_out = f"temp_{os.path.basename(f)}"
                final_video.write_videofile(temp_out, codec="libx264", audio=True, logger=None, threads=4)
                
                with open(temp_out, "rb") as vid_file:
                    zf.writestr(os.path.basename(f), vid_file.read())
                
                clip.close()
                final_video.close()
                if os.path.exists(temp_out): os.remove(temp_out)
            except Exception as e:
                st.error(f"Ошибка в файле {f}: {e}")
            progress_bar.progress((i + 1) / len(video_files))
    return zip_buf.getvalue()

# ====================== НАСТРОЙКА UI ======================
st.set_page_config(page_title="LEDsi Генератор", layout="wide", page_icon="favicon.png")

if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'video_zip_ready' not in st.session_state: st.session_state.video_zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False
if 'video_processing' not in st.session_state: st.session_state.video_processing = False

logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")
yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")

st.markdown(f"""
    <style>
    .block-container {{ max-width: 750px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    .logo-container {{ display: flex; justify-content: center; margin-bottom: 10px; }}
    .logo-img {{ width: 100px; }}
    .main-title {{ text-align: center; font-size: 1.6rem; font-weight: bold; margin-bottom: 20px; }}
    .version-text {{ text-align: center; color: #bdc3c7; font-size: 0.8rem; margin-top: 15px; }}
    div.stButton > button {{ width: 100% !important; height: 54px !important; font-weight: 600 !important; }}
    </style>
    <div class="logo-container">
        <img class="logo-img" src="data:image/png;base64,{logo_black_base64}">
    </div>
    <div class='main-title'>Генератор контента</div>
    """, unsafe_allow_html=True)

logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = [os.path.join("images", f) for f in os.listdir("images") if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []
video_files = [os.path.join("video", f) for f in os.listdir("video") if f.lower().endswith('.mp4')] if os.path.exists("video") else []

c1, c2, c3, c4 = st.columns([1, 1, 1, 1.8])
with c1: w_mm = st.number_input("Ширина", 0, value=0, on_change=reset_zip)
with c2: h_mm = st.number_input("Высота", 0, value=0, on_change=reset_zip)
with c3: pitch_str = st.text_input("Шаг", value="0", on_change=reset_zip)

tw, th = 0, 0
try:
    p_x = p_y = float(pitch_str.replace(",", ".")) if "/" not in pitch_str else 0
    if "/" in pitch_str:
        p_x, p_y = [float(x.replace(",", ".")) for x in pitch_str.split("/")]
    if w_mm > 0 and p_x > 0: tw, th = int(round(w_mm / p_x)), int(round(h_mm / p_y))
except: pass

with c4:
    logo_scale = st.slider("Размер лого %", 0, 100, 50, step=5, on_change=reset_zip)

# --- ИСПОЛНЕНИЕ ЛОГИКИ ---
if tw > 0:
    st.write(f"Разрешение: **{tw}x{th} px**")
    
    col_btns = st.columns(2)
    
    # Кнопка ФОТО
    if col_btns[0].button("📸 Создать ФОТО", use_container_width=True):
        st.session_state.processing = True
        st.session_state.video_processing = False

    # Кнопка ВИДЕО
    if col_btns[1].button("🎥 Создать ВИДЕО", use_container_width=True):
        st.session_state.video_processing = True
        st.session_state.processing = False

    # Процесс ФОТО
    if st.session_state.processing:
        with st.spinner("Генерация фото..."):
            st.session_state.zip_ready = process_images_logic(bg_files, logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
            st.session_state.processing = False
            st.rerun()

    # Процесс ВИДЕО
    if st.session_state.video_processing:
        with st.spinner("Генерация видео (это займет время)..."):
            st.session_state.video_zip_ready = process_videos_logic(video_files, logo_h_img, logo_v_img, tw, th, logo_scale)
            st.session_state.video_processing = False
            st.rerun()

    # Кнопки скачивания
    if st.session_state.zip_ready:
        st.download_button("💾 СКАЧАТЬ ФОТО (ZIP)", st.session_state.zip_ready, "photos.zip", "application/zip")
    
    if st.session_state.video_zip_ready:
        st.download_button("💾 СКАЧАТЬ ВИДЕО (ZIP)", st.session_state.video_zip_ready, "videos.zip", "application/zip")

st.markdown(f'<div class="version-text">Обновление: {yesterday_date}</div>', unsafe_allow_html=True)
