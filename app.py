import streamlit as st
import zipfile
import io
import os
import base64
from PIL import Image
from datetime import datetime

# ====================== КОНСТАНТЫ ======================
LOGO_PATH = "logo.png"
SOURCE_FOLDER = "images"

# ====================== НАСТРОЙКА ======================
st.set_page_config(page_title="LED Processor", layout="wide")

# ====================== ПУЛЕНЕПРОБИВАЕМЫЙ CSS ======================
st.markdown("""
    <style>
    /* 1. Центрирование всего контента */
    .block-container {
        max-width: 1000px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }

    /* 2. Заголовок */
    h1 {
        text-align: center !important;
        font-size: 2.25rem !important;
        margin-bottom: 30px !important;
    }

    /* 3. Принудительная обводка полей */
    div[data-testid="stNumberInput"] input {
        border: 2px solid #28a745 !important;
    }

    /* 4. Центрирование текста разрешения */
    div[data-testid="stNotification"] {
        max-width: 600px !important;
        margin: 10px auto !important;
    }
    div[data-testid="stNotification"] div[role="alert"] {
        justify-content: center !important;
        text-align: center !important;
        font-weight: bold !important;
    }

    /* 5. Стили кнопок (убираем красные обводки и тени) */
    .stButton > button, div[data-testid="stDownloadButton"] > button {
        background-color: #28a745 !important;
        color: white !important;
        border: none !important;
        height: 50px !important;
        font-size: 1rem !important;
        border-radius: 8px !important;
        width: 100% !important; /* Кнопка займет всю ширину своей колонки */
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== ЗАГОЛОВОК ======================
st.markdown("<h1>Создать контент для LED-экрана</h1>", unsafe_allow_html=True)

# Контейнер для превью
preview_placeholder = st.container()

# ====================== ВВОД ДАННЫХ ======================
# Делаем сетку ввода
c1, c2, c3, c4 = st.columns([2, 2, 2, 3])

with c1:
    w_mm = st.number_input("Ширина (мм)", min_value=0, value=0, step=10)
with c2:
    h_mm = st.number_input("Высота (мм)", min_value=0, value=0, step=10)
with c3:
    pitch = st.number_input("Шаг пикселя (мм)", min_value=0, value=0, step=1)
with c4:
    logo_percent = st.slider("Размер логотипа в %", 0, 150, 60, 5)

# Проверка заполнения
fields_ready = w_mm > 0 and h_mm > 0 and pitch > 0

# ====================== ОБРАБОТКА И ПРЕВЬЮ ======================
if fields_ready:
    tw = int(round(w_mm / pitch))
    th = int(round(h_mm / pitch))
    
    with preview_placeholder:
        # Логика обработки картинки (упрощенно для примера)
        if os.path.exists(LOGO_PATH):
            bg_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            if bg_files:
                # Показываем превью и разрешение
                st.markdown(f'<div style="text-align:center; margin-bottom:10px;">'
                            f'<div style="max-width:600px; margin:0 auto; background:#f0f0f0; border-radius:8px; padding:20px; color:#666;">'
                            f'Превью контента {tw}x{th}</div></div>', unsafe_allow_html=True)
                
                # Плашка разрешения ПОД превью
                st.success(f"Разрешение: {tw} × {th} px")

# ====================== ЦЕНТРИРОВАННАЯ КНОПКА ======================
st.write("") # Отступ

if fields_ready:
    # СОЗДАЕМ ТРИ КОЛОНКИ: Пустая (1) | Кнопка (2) | Пустая (1)
    # Это гарантирует, что кнопка будет ВСЕГДА по центру текста h1
    _, btn_col, _ = st.columns([1, 2, 1])
    
    with btn_col:
        if "zip_ready" not in st.session_state:
            st.session_state.zip_ready = False

        if not st.session_state.zip_ready:
            if st.button("Генерировать контент"):
                with st.spinner("Создание..."):
                    # Здесь ваша логика генерации архива
                    # ...
                    st.session_state.zip_ready = True
                    st.rerun()
        else:
            # После генерации кнопка заменяется на скачивание
            st.download_button(
                label="Скачать архив",
                data=b"dummy data", # Здесь ваш zip_buffer
                file_name="LED_content.zip",
                mime="application/zip"
            )
            if st.button("Сбросить"): # Опционально: кнопка для возврата назад
                st.session_state.zip_ready = False
                st.rerun()
