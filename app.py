import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image, ImageOps
from datetime import datetime, timedelta
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip

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
                return base64.b64encode(f.read()).decode()
        except: return ""
    return ""

def process_single_image(bg_path, logo_img, tw, th, scale_percent):
    try:
        with Image.open(bg_path) as img:
            img = ImageOps.fit(img.convert("RGB"), (tw, th), Image.Resampling.LANCZOS)
            lw, lh = logo_img.size
            max_scale = min(tw / lw, th / lh)
            final_scale = max_scale * (scale_percent / 100)
            new_lw, new_lh = max(1, int(lw * final_scale)), max(1, int(lh * final_scale))
            logo_res = logo_img.resize((new_lw, new_lh), Image.Resampling.LANCZOS)
            img.paste(logo_res, ((tw - new_lw)//2, (th - new_lh)//2), logo_res)
            
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=95)
            return buf.getvalue()
    except: return None

def process_video_file(v_path, logo_path, tw, th, scale_percent):
    try:
        clip = VideoFileClip(v_path).without_audio()
        # Масштабирование видео (Fill)
        sc = max(tw / clip.w, th / clip.h)
        new_w, new_h = int(clip.w * sc), int(clip.h * sc)
        clip_res = clip.resized((new_w, new_h))
        clip_crop = clip_res.cropped(x_center=new_w/2, y_center=new_h/2, width=tw, height=th)
        
        # Наложение лого
        logo = (ImageClip(logo_path)
                .with_duration(clip.duration)
                .resized(width=tw * (scale_percent/100))
                .with_position(("center", "center")))
        
        final = CompositeVideoClip([clip_crop, logo])
        out_p = f"temp_{os.path.basename(v_path)}"
        
        # Рендеринг с битрейтом 5000k
        final.write_videofile(
            out_p, 
            fps=25, 
            codec="libx264", 
            bitrate="5000k", 
            preset="ultrafast", 
            logger=None
        )
        
        with open(out_p, "rb") as f:
            data = f.read()
        os.remove(out_p)
        return data
    except: return None

# ====================== ИНТЕРФЕЙС ======================

st.set_page_config(page_title="LEDsi Генератор", layout="centered", page_icon="favicon.png")

# Состояния
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None
if 'processing' not in st.session_state: st.session_state.processing = False

# Загрузка логотипов
logo_h_img = get_cached_logo("logo.png")
logo_v_img = get_cached_logo("logo.png")
main_logo_b64 = get_base64_img("logo_h.png") # Тот, что в шапке

# Твой CSS
st.markdown(f"""
    <style>
    .logo-container {{ display: flex; justify-content: center; margin-bottom: 0px; }}
    .logo-img {{ width: 120px; }}
    .title {{ text-align: center; font-weight: bold; font-size: 22px; margin-top: -10px; }}
    div.stButton > button {{ border-radius: 10px; height: 55px; font-weight: bold; font-size: 16px; }}
    </style>
    <div class="logo-container">
        <img class="logo-img" src="data:image/png;base64,{main_logo_b64}">
    </div>
    <div class="title">Генератор контента</div>
""", unsafe_allow_html=True)

# Ввод параметров
c1, c2, c3 = st.columns(3)
with c1: w_mm = st.number_input("Ширина", value=8000)
with c2: h_mm = st.number_input("Высота", value=6000)
with c3: pitch = st.number_input("Шаг", value=10.0, step=0.1)

logo_scale = st.slider("Размер логотипа %", 5, 100, 50, step=5)

# Итоговое разрешение
tw, th = int(w_mm / pitch), int(h_mm / pitch)

# --- КНОПКИ УПРАВЛЕНИЯ ---
st.markdown("<br>", unsafe_allow_html=True)
btn_col1, btn_col2 = st.columns(2)

mode = None
if btn_col1.button(f"Создать фото {tw}x{th} px", type="primary", use_container_width=True):
    mode = "photo"
if btn_col2.button(f"Создать видео {tw}x{th} px", type="primary", use_container_width=True):
    mode = "video"

# Логика обработки
if mode:
    folder = "videos" if mode == "video" else "images"
    if not os.path.exists(folder): os.makedirs(folder)
    
    exts = ('.mp4', '.mov') if mode == "video" else ('.jpg', '.jpeg', '.png')
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]

    if not files:
        st.error(f"Добавьте файлы в папку '{folder}' на сервере!")
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            progress_bar = st.progress(0)
            status = st.empty()
            
            for i, f_path in enumerate(files):
                status.text(f"Обработка {i+1}/{len(files)}...")
                
                if mode == "video":
                    data = process_video_file(f_path, "logo.png", tw, th, logo_scale)
                    new_name = os.path.splitext(os.path.basename(f_path))[0] + ".mp4"
                else:
                    active_logo = logo_h_img if tw >= th else logo_v_img
                    data = process_single_image(f_path, active_logo, tw, th, logo_scale)
                    new_name = os.path.basename(f_path)
                
                if data:
                    zf.writestr(new_name, data)
                progress_bar.progress((i + 1) / len(files))
        
        st.session_state.zip_ready = zip_buffer.getvalue()
        status.success("Готово! Архив сформирован.")

# Кнопка скачивания
if st.session_state.zip_ready:
    st.download_button(
        label="📥 СКАЧАТЬ КОНТЕНТ (ZIP)",
        data=st.session_state.zip_ready,
        file_name=f"content_{tw}x{th}.zip",
        mime="application/zip",
        use_container_width=True
    )

# Подвал
st.markdown(f"<div style='text-align:center; color:grey; font-size:12px; margin-top:50px;'>Версия 0.0.9. Обновление контента от {datetime.now().strftime('%d.%m.%Y')}</div>", unsafe_allow_html=True)
