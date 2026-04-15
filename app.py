import streamlit as st
import zipfile, io, os, base64
from PIL import Image, ImageOps
from datetime import datetime

# Настройка страницы СРАЗУ
st.set_page_config(page_title="LED Gen", layout="wide")

# Функции с заглушками на случай ошибок
def get_image_list(folder):
    if not os.path.exists(folder): os.makedirs(folder, exist_ok=True)
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

def process_single_image(bg_path, logo_h, logo_v, tw, th, scale):
    if tw <= 0 or th <= 0: return None
    try:
        active_logo = logo_h if tw >= th else logo_v
        if not active_logo: return None
        with Image.open(bg_path) as img:
            img = ImageOps.fit(img.convert("RGB"), (tw, th), Image.Resampling.LANCZOS)
            lw, lh = active_logo.size
            final_scale = min(tw/lw, th/lh) * (scale/100)
            logo_res = active_logo.resize((max(1, int(lw*final_scale)), max(1, int(lh*final_scale))), Image.Resampling.LANCZOS)
            img.paste(logo_res, ((tw-logo_res.size[0])//2, (th-logo_res.size[1])//2), logo_res)
            return img
    except: return None

# Ресурсы
logo_h_img = None
if os.path.exists("logo_h.png"): logo_h_img = Image.open("logo_h.png").convert("RGBA")
logo_v_img = None
if os.path.exists("logo_v.png"): logo_v_img = Image.open("logo_v.png").convert("RGBA")
bg_files = get_image_list("images")

# Интерфейс
st.title("Генератор контента")

c1, c2, c3 = st.columns(3)
w = c1.number_input("Ширина мм", 0)
h = c2.number_input("Высота мм", 0)
p = c3.number_input("Шаг мм", 0.0, step=0.1, format="%g")

tw, th = (int(w/p), int(h/p)) if (w and h and p) else (0, 0)
scale = st.slider("Лого %", 5, 100, 50)

if tw > 0 and bg_files:
    res = process_single_image(bg_files[0], logo_h_img, logo_v_img, tw, th, scale)
    if res:
        st.image(res, caption=f"Превью: {tw}x{th}px")
        
        if st.button("ГЕНЕРИРОВАТЬ ВСЁ"):
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as zf:
                for f in bg_files:
                    img = process_single_image(f, logo_h_img, logo_v_img, tw, th, scale)
                    if img:
                        img_buf = io.BytesIO()
                        img.save(img_buf, format="JPEG", quality=90)
                        zf.writestr(os.path.basename(f), img_buf.getvalue())
            
            st.download_button("СКАЧАТЬ ZIP", buf.getvalue(), f"{tw}x{th}.zip", "application/zip")
else:
    st.info("Введите параметры и проверьте папку images")
