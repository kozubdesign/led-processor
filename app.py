import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps
from datetime import datetime, timedelta

# === ДОБАВЛЕНО ДЛЯ ВИДЕО ===
import moviepy.editor as mpy
import numpy as np   # ← Добавили эту строку

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

# ====================== ИСПРАВЛЕННАЯ ФУНКЦИЯ ДЛЯ ВИДЕО ======================
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

        # === ИСПРАВЛЕНИЕ: переводим PIL в numpy-массив ===
        logo_array = np.array(logo_resized)

        logo_clip = mpy.ImageClip(logo_array)          # ← Вот здесь было главное исправление
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

        # Закрываем ресурсы
        video.close()
        final_video.close()
        logo_clip.close()

        return output_io.getvalue()

    except Exception as e:
        st.error(f"Ошибка при обработке **{os.path.basename(video_path)}**: {str(e)}")
        return None

# ====================== НАСТРОЙКА UI (остальное без изменений) ======================
st.set_page_config(page_title="LEDsi Генератор контента", layout="wide", page_icon="favicon.png")

logo_black_base64 = get_base64_img("logo_black.png")
logo_h_base64 = get_base64_img("logo_h.png")

yesterday_date = (datetime.now() - timedelta(days=1)).strftime("%d.%m.%Y")

# (Ваш большой блок CSS и HTML остаётся точно таким же, как было)

st.markdown(f"""
    <style>
    /* ... ваш весь CSS без изменений ... */
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

# ... (весь блок с колонками c1,c2,c3,c4 и расчётом tw, th, logo_scale остаётся без изменений) ...

# ====================== БЛОК КНОПОК ======================
st.markdown("<br>", unsafe_allow_html=True)
action_placeholder = st.empty()

if tw > 0 and (logo_h_img or logo_v_img):

    col1, col2 = st.columns(2)

    with col1:
        if bg_files:
            res_text = f"{tw}х{th} px"
            if st.session_state.zip_ready:
                current_date = datetime.now().strftime("%y_%m_%d")
                zip_filename = f"{tw}x{th}_{current_date}.zip"
                st.download_button(label="Скачать архив", data=st.session_state.zip_ready, file_name=zip_filename, mime="application/zip", type="primary")
            elif st.session_state.processing:
                # ваш оригинальный код генерации изображений (оставлен как был)
                zip_buffer = io.BytesIO()
                total_files = len(bg_files)
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for i, f in enumerate(bg_files):
                        percent = int(((i + 1) / total_files) * 100)
                        st.button(f"Идет генерация... {percent}%", disabled=True, key=f"btn_proc_{i}")
                        processed = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
                        if processed:
                            img_byte_arr = io.BytesIO()
                            processed.save(img_byte_arr, format='JPEG', quality=95)
                            zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
                st.session_state.zip_ready = zip_buffer.getvalue()
                st.session_state.processing = False
                st.rerun()
            else:
                if st.button(f"Создать контент {res_text}", type="primary"):
                    st.session_state.processing = True
                    st.rerun()

    with col2:
        if video_files:
            if st.session_state.zip_ready_video:
                current_date = datetime.now().strftime("%y_%m_%d")
                zip_filename = f"video_{tw}x{th}_{current_date}.zip"
                st.download_button(label="Скачать видео", data=st.session_state.zip_ready_video, file_name=zip_filename, mime="application/zip", type="secondary")
            else:
                if st.button("Создать видео-контент", type="secondary"):
                    with st.spinner("Обрабатываем видео..."):
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for vpath in video_files:
                                video_data = process_video(vpath, logo_h_img, logo_v_img, tw, th, logo_scale)
                                if video_data:
                                    name = os.path.splitext(os.path.basename(vpath))[0]
                                    zip_file.writestr(f"{name}_{tw}x{th}.mp4", video_data)
                        st.session_state.zip_ready_video = zip_buffer.getvalue()
                        st.success("Видео успешно обработаны!")
                        st.rerun()

# Подпись версии
st.markdown(f'<div class="version-text">Версия 0.0.83 (видео исправлено). Обновление контента от {yesterday_date}</div>', unsafe_allow_html=True)
