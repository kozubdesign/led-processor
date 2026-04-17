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

def reset_zip():
    st.session_state.zip_ready = None

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

def process_video_file(v_path, logo_path, tw, th, scale_percent, fps, bitrate):
    try:
        clip = VideoFileClip(v_path).without_audio()
        # Масштабирование Fill (покрытие всего экрана)
        sc = max(tw / clip.w, th / clip.h)
        new_w, new_h = int(clip.w * sc), int(clip.h * sc)
        clip_res = clip.resized((new_w, new_h))
        clip_crop = clip_res.cropped(x_center=new_w/2, y_center=new_h/2, width=tw, height=th)
        
        # Логотип (центрирование)
        logo = (ImageClip(logo_path)
                .with_duration(clip.duration)
                .resized(width=tw * (scale_percent/100))
                .with_position(("center", "center")))
        
        final = CompositeVideoClip([clip_crop, logo])
        out_p = f"temp_{os.path.basename(v_path)}"
        
        # Рендеринг (настройки для локального сервера)
        final.write_videofile(
            out_p, 
            fps=fps, 
            codec="libx264", 
            bitrate=f"{bitrate}k",
            preset="medium", 
            threads=8, 
            logger=None
        )
        
        with open(out_p, "rb") as f:
            data = f.read()
        os.remove(out_p)
        return data
    except Exception as e:
        print(f"Ошибка видео: {e}")
        return None

# ====================== ИНТЕРФЕЙС ======================

st.set_page_config(page_title="LEDsi PRO Generator", layout="wide")

# CSS для красоты
st.markdown("""
    <style>
    .main-title { text-align: center; font-size: 2rem; font-weight: bold; color: #1E1E1E; }
    .stButton > button { width: 100%; height: 60px; background-color: #28a745; color: white; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<div class='main-title'>LEDsi PRO Content Generator</div>", unsafe_allow_html=True)

# Инициализация
if 'zip_ready' not in st.session_state: st.session_state.zip_ready = None

# Сайдбар с настройками качества
with st.sidebar:
    st.header("⚙️ Настройки качества")
    content_type = st.radio("Тип контента:", ["Фото", "Видео"], on_change=reset_zip)
    target_fps = st.slider("Кадров в секунду (FPS)", 24, 60, 25, step=1, help="60 FPS для плавного видео")
    target_bitrate = st.select_slider("Битрейт (kbps)", options=[500, 2000, 5000, 10000, 20000], value=5000)

# Параметры экрана
c1, c2, c3, c4 = st.columns([1, 1, 1, 1.8])
with c1: w_px = st.number_input("Ширина (пикс)", 1, value=1920)
with c2: h_px = st.number_input("Высота (пикс)", 1, value=1080)
with c3: l_scale = st.slider("Размер лого %", 5, 100, 50, step=5)

# Пути
is_v_mode = (content_type == "Видео")
folder = "videos" if is_v_mode else "images"
if not os.path.exists(folder): os.makedirs(folder)

exts = ('.mp4', '.mov', '.avi', '.mkv') if is_v_mode else ('.jpg', '.jpeg', '.png')
files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(exts)]

# Превью
if files:
    with st.expander("👁️ Предпросмотр первого файла", expanded=True):
        active_logo = get_cached_logo("logo.png")
        if active_logo:
            try:
                if is_v_mode:
                    with VideoFileClip(files[0]) as clip:
                        frame = clip.get_frame(0)
                        img_prev = Image.fromarray(frame)
                else:
                    img_prev = Image.open(files[0]).convert("RGB")
                
                img_prev = ImageOps.fit(img_prev, (w_px, h_px))
                # Масштабируем лого для превью
                lw, lh = active_logo.size
                ms = min(w_px/lw, h_px/lh) * (l_scale/100)
                logo_p = active_logo.resize((int(lw*ms), int(lh*ms)), Image.Resampling.LANCZOS)
                img_prev.paste(logo_p, ((w_px-logo_p.width)//2, (h_px-logo_p.height)//2), logo_p)
                st.image(img_prev, use_container_width=True)
            except: st.error("Не удалось создать превью")

# Кнопка запуска
if files:
    if st.button(f"🚀 ОБРАБОТАТЬ ВСЁ ({len(files)} шт.)"):
        zip_buf = io.BytesIO()
        progress = st.progress(0)
        status = st.empty()
        
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for i, f_path in enumerate(files):
                status.markdown(f"⏳ **Обработка:** `{os.path.basename(f_path)}`")
                
                if is_v_mode:
                    data = process_video_file(f_path, "logo.png", w_px, h_px, l_scale, target_fps, target_bitrate)
                    name = os.path.splitext(os.path.basename(f_path))[0] + ".mp4"
                else:
                    logo_img = get_cached_logo("logo.png")
                    data = process_single_image(f_path, logo_img, w_px, h_px, l_scale)
                    name = os.path.basename(f_path)
                
                if data:
                    zf.writestr(name, data)
                progress.progress((i + 1) / len(files))
        
        st.session_state.zip_ready = zip_buf.getvalue()
        status.success(f"✅ Готово! Все файлы ({len(files)} шт.) обработаны.")
        st.rerun()
else:
    st.warning(f"Папка '{folder}' пуста. Добавьте в неё файлы и обновите страницу.")

# Скачивание
if st.session_state.zip_ready:
    st.download_button(
        label="📥 СКАЧАТЬ ВЕСЬ КОНТЕНТ (ZIP)",
        data=st.session_state.zip_ready,
        file_name=f"LED_CONTENT_{w_px}x{h_px}.zip",
        mime="application/zip"
    )
