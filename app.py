# ====================== БЛОК КНОПОК ======================
st.markdown("<br>", unsafe_allow_html=True)

# Создаем две колонки для кнопок
btn_col1, btn_col2 = st.columns(2)

if tw > 0 and (logo_h_img or logo_v_img):
    res_text = f"{tw}х{th} px"
    
    # КНОПКА ФОТО
    with btn_col1:
        if st.button(f"Создать ФОТО {res_text}", type="primary", use_container_width=True):
            st.session_state.processing_mode = "photo"
            st.session_state.processing = True
            st.rerun()

    # КНОПКА ВИДЕО
    with btn_col2:
        if st.button(f"Создать ВИДЕО {res_text}", type="primary", use_container_width=True):
            st.session_state.processing_mode = "video"
            st.session_state.processing = True
            st.rerun()

# Логика обработки (вставляется выше или ниже кнопок)
if st.session_state.processing:
    mode = st.session_state.get('processing_mode', 'photo')
    folder = "videos" if mode == "video" else "images"
    
    # Проверяем файлы
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(
        ('.mp4', '.mov') if mode == "video" else ('.jpg', '.jpeg', '.png')
    )] if os.path.exists(folder) else []

    if not files:
        st.error(f"Папка {folder} пуста!")
        st.session_state.processing = False
    else:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            progress_bar = st.progress(0)
            for i, f_path in enumerate(files):
                if mode == "video":
                    # Вызываем функцию для видео (которую мы написали ранее)
                    data = process_video_file(f_path, "logo.png", tw, th, logo_scale, target_fps=25, bitrate=5000)
                else:
                    # Вызываем старую функцию для фото
                    data = process_single_image(f_path, logo_h_img if tw >= th else logo_v_img, tw, th, logo_scale)
                
                if data:
                    name = os.path.basename(f_path)
                    if mode == "video": name = os.path.splitext(name)[0] + ".mp4"
                    zf.writestr(name, data)
                progress_bar.progress((i + 1) / len(files))
        
        st.session_state.zip_ready = zip_buffer.getvalue()
        st.session_state.processing = False
        st.rerun()

# Кнопка скачивания появится после генерации
if st.session_state.zip_ready:
    st.download_button(
        label="📥 СКАЧАТЬ ГОТОВЫЙ АРХИВ",
        data=st.session_state.zip_ready,
        file_name=f"content_{tw}x{th}.zip",
        mime="application/zip",
        use_container_width=True
    )
