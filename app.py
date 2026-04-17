import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps
from datetime import datetime, timedelta

# Для видео
import moviepy.editor as mpy
import numpy as np

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
    if 'zip_ready_video' in st.session_state:
        st.session_state.zip_ready_video = None

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

# ====================== ФУНКЦИЯ ДЛЯ ВИДЕО ======================
def process_video(video_path, logo_h, logo_v, tw, th, logo_scale):
    try:
        video = mpy.VideoFileClip(video_path)
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo:
            video.close()
            return None

        lw, lh = active_logo.size
        max_scale = min(tw / lw, th / lh)
        final_scale = max_scale * (logo_scale / 100)
        new_lw = max(1, int(lw * final_scale))
        new_lh = max(1, int(lh * final_scale))

        logo_resized = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
        logo_array = np.array(logo_resized)

        logo_clip = mpy.ImageClip(logo_array)
        logo_clip = logo_clip.set_duration(video.duration)
        logo_clip = logo_clip.set_position("center")

        final_video = mpy.CompositeVideoClip([video, logo_clip])

        output_io = io.BytesIO()
        final_video.write_videofile(
            output_io,
            codec="libx264",
            audio_codec="aac",
            fps=video.fps or 30,
            preset="medium",
            bitrate="8000k",
            verbose=False,
            logger=None
        )
        output_io.seek(0)

        video.close()
        final_video.close()
        logo_clip.close()

        return output_io.getvalue()

    except Exception as e:
        st.error(f"Ошибка при обработке **{os.path.basename(video_path)}**: {str(e)}")
        return None

# ====================== НАСТРОЙКА UI ======================
st.set_page_config(page_title="LEDsi Генератор контента", layout="wide", page_icon="favicon.png")

logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")

yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")

st.markdown(f"""
    <style>
    div[data-testid="stNumberInput"] button {{ display: none !important; }}
    input::-webkit-outer-spin-button, input::-webkit-inner-spin-button {{ -webkit-appearance: none !important; margin: 0 !important; }}
    input[type=number] {{ -moz-appearance: textfield !important; }}
    .block-container {{ max-width: 750px !important; margin: 0 auto !important; padding-top: 1rem !important; }}
    [data-testid="stHeader"] {{ display: none; }}
    [data-testid="column"] {{ min-width: 0px !important; flex: 1 1 0% !important; }}
    div[data-testid="stNumberInput"], div[data-testid="stTextInput"], .stSlider {{ width: 100% !important; }}
    .logo-container {{ display: flex; justify-content: center; margin-top: 10px; margin-bottom: 10px; }}
    .logo-img {{ width: 100px; }}
    .preview-img {{ max-width: 100%; max-height: 250px; border-radius: 8px; border: 1px solid #ddd; }}
    .preview-placeholder {{
        width: 100%; height: 250px; background-color: #f8f9fa; border: 2px dashed #dce0e4;
        border-radius: 8px; display: flex; align-items: center; justify-content: center;
        color: #adb5bd; font-weight: 500; margin-bottom: 20px;
        text-transform: uppercase; letter-spacing: 1px;
    }}
    .version-text {{ text-align: center; color: #bdc3c7; font-size: 0.8rem; margin-top: 15px; }}
    @media (max-width: 768px) {{ .preview-img, .preview-placeholder {{ max-height: 200px !important; }} }}
    </style>
    <div class="logo-container">
        <img class="logo-img logo-light" src="data:image/png;base64,{logo_black_base64}">
        <img class="logo-img logo-dark" src="data:image/png;base64,{logo_h_base64}">
    </div>
    <div class='main-title'>Генератор контента</div>
    """, unsafe_allow_html=True)

if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'zip_ready_video' not in st.session_state: st.session_state.zip_ready_video = None
if 'processing' not in st.session_state: st.session_state.processing = False

preview_placeholder = st.empty()

logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")
bg_files = [os.path.join("images", f) for f in os.listdir("images") if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []
video_files = [os.path.join("video", f) for f in os.listdir("video") if f.lower().endswith(('.mp4', '.mov', '.avi'))] if os.path.exists("video") else []

# ====================== Параметры ======================
c1, c2, c3, c4 = st.columns([1, 1, 1, 1.8])
with c1: w_mm = st.number_input("Ширина", 0, value=0, on_change=reset_zip)
with c2: h_mm = st.number_input("Высота", 0, value=0, on_change=reset_zip)
with c3: pitch_str = st.text_input("Шаг", value="0", on_change=reset_zip)

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
except: pass

if w_mm > 0 and h_mm > 0 and pitch_x > 0 and pitch_y > 0:
    tw = int(round(w_mm / pitch_x))
    th = int(round(h_mm / pitch_y))

with c4:
    logo_scale = st.slider("Размер логотипа %", 0, 100, 50, step=5, on_change=reset_zip)

# Превью
if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    preview = get_processed_preview(bg_files[0], logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
    if preview:
        buf = io.BytesIO()
        preview.save(buf, format="JPEG", quality=75)
        img_str = base64.b64encode(buf.getvalue()).decode()
        preview_placeholder.markdown(f'''
            <div style="display: flex; justify-content: center; margin-bottom: 20px;">
                <img class="preview-img" src="data:image/jpeg;base64,{img_str}">
            </div>
        ''', unsafe_allow_html=True)
else:
    preview_placeholder.markdown('''
        <div style="display: flex; justify-content: center; margin-bottom: 20px;">
            <div class="preview-placeholder">Тут будет превью</div>
        </div>
    ''', unsafe_allow_html=True)

# ====================== КНОПКИ ======================
st.markdown("<br>", unsafe_allow_html=True)

if tw > 0 and (logo_h_img or logo_v_img):
    col1, col2 = st.columns(2)

    with col1:   # Кнопка для изображений (как было)
        if bg_files:
            res_text = f"{tw}х{th} px"
            if st.session_state.zip_ready:
                current_date = datetime.now().strftime("%y_%m_%d")
                st.download_button("Скачать архив", data=st.session_state.zip_ready, 
                                 file_name=f"{tw}x{th}_{current_date}.zip", mime="application/zip", type="primary")
            elif st.session_state.processing:
                # ... ваш оригинальный блок обработки изображений ...
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for i, f in enumerate(bg_files):
                        st.button(f"Идет генерация... {int((i+1)/len(bg_files)*100)}%", disabled=True)
                        processed = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
                        if processed:
                            buf = io.BytesIO()
                            processed.save(buf, format='JPEG', quality=95)
                            zf.writestr(os.path.basename(f), buf.getvalue())
                st.session_state.zip_ready = zip_buffer.getvalue()
                st.session_state.processing = False
                st.rerun()
            else:
                if st.button(f"Создать контент {res_text}", type="primary"):
                    st.session_state.processing = True
                    st.rerun()

    with col2:   # ← Кнопка для видео слева от основной
        if video_files:
            if st.session_state.zip_ready_video:
                current_date = datetime.now().strftime("%y_%m_%d")
                st.download_button("Скачать видео", data=st.session_state.zip_ready_video,
                                 file_name=f"video_{tw}x{th}_{current_date}.zip", mime="application/zip", type="secondary")
            else:
                if st.button("Создать видео-контент", type="secondary"):
                    with st.spinner("Обрабатываем видео..."):
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                            for vpath in video_files:
                                data = process_video(vpath, logo_h_img, logo_v_img, tw, th, logo_scale)
                                if data:
                                    name = os.path.splitext(os.path.basename(vpath))[0]
                                    zf.writestr(f"{name}_{tw}x{th}.mp4", data)
                        st.session_state.zip_ready_video = zip_buffer.getvalue()
                        st.success("Видео готовы!")
                        st.rerun()

st.markdown(f'<div class="version-text">Версия 0.0.83. Обновление от {yesterday_date}</div>', unsafe_allow_html=True)
