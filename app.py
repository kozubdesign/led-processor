import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps
from datetime import datetime, timedelta

# Импорты для работы с видео
import moviepy.editor as mpy

# ====================== ФУНКЦИИ ======================
@st.cache_resource
def get_cached_logo(path):
    if os.path.exists(path):
        try: 
            return Image.open(path).convert("RGBA")
        except: 
            return None
    return None

def get_base64_img(path):
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                data = f.read()
            return base64.b64encode(data).decode()
        except: 
            return ""
    return ""

def reset_zip():
    st.session_state.zip_ready = None
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
    except: 
        return None

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
    except: 
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

# Инициализация состояния
if 'zip_ready' not in st.session_state: 
    st.session_state.zip_ready = None
if 'zip_ready_video' not in st.session_state: 
    st.session_state.zip_ready_video = None
if 'processing' not in st.session_state: 
    st.session_state.processing = False

preview_placeholder = st.empty()

logo_h_img = get_cached_logo("logo_h.png")
logo_v_img = get_cached_logo("logo_v.png")

# Файлы изображений
bg_files = [os.path.join("images", f) for f in os.listdir("images") 
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))] if os.path.exists("images") else []

# Файлы видео — исправлено название папки
video_files = [os.path.join("video", f) for f in os.listdir("video") 
               if f.lower().endswith(('.mp4', '.mov', '.avi'))] if os.path.exists("video") else []

# ====================== Основные параметры ======================
c1, c2, c3, c4 = st.columns([1, 1, 1, 1.8])
with c1: 
    w_mm = st.number_input("Ширина (мм)", 0, value=0, on_change=reset_zip)
with c2: 
    h_mm = st.number_input("Высота (мм)", 0, value=0, on_change=reset_zip)
with c3: 
    pitch_str = st.text_input("Шаг (pitch)", value="0", on_change=reset_zip)

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
    tw = int(round(w_mm / pitch_x))
    th = int(round(h_mm / pitch_y))

with c4:
    logo_scale = st.slider(
        "Размер логотипа %",
        0, 100,
        50,
        step=5,
        on_change=reset_zip,
        key="logo_scale_slider"
    )

# Превью изображения
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

# ====================== Генерация изображений ======================
st.markdown("<br>", unsafe_allow_html=True)
img_action_placeholder = st.empty()

if tw > 0 and (logo_h_img or logo_v_img) and bg_files:
    res_text = f"{tw}×{th} px"
    
    if st.session_state.zip_ready:
        current_date = datetime.now().strftime("%y_%m_%d")
        zip_filename = f"{tw}x{th}_{current_date}.zip"
        img_action_placeholder.download_button(
            label="Скачать архив с изображениями",
            data=st.session_state.zip_ready,
            file_name=zip_filename,
            mime="application/zip",
            type="primary"
        )
    elif st.session_state.processing:
        zip_buffer = io.BytesIO()
        total_files = len(bg_files)
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, f in enumerate(bg_files):
                percent = int(((i + 1) / total_files) * 100)
                img_action_placeholder.button(f"Идет генерация... {percent}%", disabled=True, key=f"btn_img_{i}")
                processed = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
                if processed:
                    img_byte_arr = io.BytesIO()
                    processed.save(img_byte_arr, format='JPEG', quality=95)
                    zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
        st.session_state.zip_ready = zip_buffer.getvalue()
        st.session_state.processing = False
        st.rerun()
    else:
        if img_action_placeholder.button(f"Создать контент {res_text}", type="primary"):
            st.session_state.processing = True
            st.rerun()

# ====================== Генерация видео ======================
st.markdown("---")
st.subheader("🎥 Генерация видеоконтента")

video_action_placeholder = st.empty()

if tw > 0 and (logo_h_img or logo_v_img) and video_files:
    video_res_text = f"{tw}×{th} px • {len(video_files)} видео"

    if st.session_state.zip_ready_video:
        current_date = datetime.now().strftime("%y_%m_%d")
        zip_filename = f"LEDsi_video_{tw}x{th}_{current_date}.zip"
        video_action_placeholder.download_button(
            label="Скачать архив с видео",
            data=st.session_state.zip_ready_video,
            file_name=zip_filename,
            mime="application/zip",
            type="primary"
        )
    else:
        if video_action_placeholder.button(f"Создать видео-контент ({video_res_text})", 
                                          type="secondary", 
                                          use_container_width=True):
            with st.spinner("Обрабатываем видео... Это может занять несколько минут"):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for video_path in video_files:
                        try:
                            video = mpy.VideoFileClip(video_path)
                            
                            active_logo = logo_h_img if tw >= th else logo_v_img
                            if not active_logo:
                                continue

                            lw, lh = active_logo.size
                            max_scale = min(tw / lw, th / lh)
                            final_scale = max_scale * (logo_scale / 100)
                            new_lw = max(1, int(lw * final_scale))
                            new_lh = max(1, int(lh * final_scale))

                            logo_pil = active_logo.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
                            logo_bytes = io.BytesIO()
                            logo_pil.save(logo_bytes, format="PNG")
                            logo_bytes.seek(0)

                            logo_clip = (mpy.ImageClip(logo_bytes.getvalue())
                                       .set_duration(video.duration)
                                       .set_position("center"))

                            final_video = mpy.CompositeVideoClip([video, logo_clip])

                            output_bytes = io.BytesIO()
                            final_video.write_videofile(
                                output_bytes,
                                codec="libx264",
                                audio_codec="aac",
                                fps=video.fps or 30,
                                preset="medium",      # "fast" — быстрее, но хуже качество
                                bitrate="8000k",
                                verbose=False,
                                logger=None
                            )
                            output_bytes.seek(0)

                            name_without_ext = os.path.splitext(os.path.basename(video_path))[0]
                            zip_file.writestr(f"{name_without_ext}_{tw}x{th}.mp4", output_bytes.getvalue())

                            video.close()
                            final_video.close()

                        except Exception as e:
                            st.error(f"Ошибка при обработке {os.path.basename(video_path)}: {str(e)}")

                st.session_state.zip_ready_video = zip_buffer.getvalue()
                st.success("✅ Видео успешно обработаны и добавлены в архив!")
                st.rerun()

else:
    if not video_files:
        st.info("Папка **video** пуста или не найдена. Положите туда MP4-файлы.")
    elif tw == 0:
        st.info("Укажите ширину, высоту и шаг пикселей для генерации видео.")

# Подпись версии
st.markdown(f'<div class="version-text">Версия 0.0.82 (с видео). Обновление контента от {yesterday_date}</div>', 
            unsafe_allow_html=True)
