# ====================== БЛОК КНОПОК (ИСПРАВЛЕННЫЙ) ======================
st.markdown("<br>", unsafe_allow_html=True)

# Контейнеры для кнопок, чтобы они не прыгали
photo_container = st.empty()
video_container = st.empty()

res_text = f"{tw}х{th} px" if tw > 0 else ""

if tw > 0 and (logo_h_img or logo_v_img):
    
    # --- ЛОГИКА ФОТО ---
    if bg_files:
        if st.session_state.zip_ready:
            photo_container.download_button(
                label="Скачать архив (ФОТО)", 
                data=st.session_state.zip_ready, 
                file_name=f"{tw}x{th}_{datetime.now().strftime('%y_%m_%d')}.zip", 
                mime="application/zip", type="primary", key="down_photo"
            )
        elif st.session_state.processing:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for i, f in enumerate(bg_files):
                    percent = int(((i + 1) / len(bg_files)) * 100)
                    photo_container.button(f"Обработка фото... {percent}%", disabled=True, key=f"btn_p_proc_{i}")
                    processed = process_single_image(f, logo_h_img, logo_v_img, tw, th, logo_scale, w_mm, h_mm)
                    if processed:
                        img_byte_arr = io.BytesIO()
                        processed.save(img_byte_arr, format='JPEG', quality=95)
                        zip_file.writestr(os.path.basename(f), img_byte_arr.getvalue())
            st.session_state.zip_ready = zip_buffer.getvalue()
            st.session_state.processing = False
            st.rerun()
        else:
            if photo_container.button(f"Создать фото контент {res_text}", type="secondary", key="run_photo_gen"):
                st.session_state.processing = True
                st.session_state.video_processing = False # Отключаем видео, если нажали фото
                st.rerun()

    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

    # --- ЛОГИКА ВИДЕО ---
    if video_files:
        if st.session_state.video_zip_ready:
            video_container.download_button(
                label="Скачать архив (ВИДЕО)", 
                data=st.session_state.video_zip_ready, 
                file_name=f"video_{tw}x{th}_{datetime.now().strftime('%y_%m_%d')}.zip", 
                mime="application/zip", type="primary", key="down_video"
            )
        elif st.session_state.video_processing:
            v_zip_buffer = io.BytesIO()
            with zipfile.ZipFile(v_zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for i, f in enumerate(video_files):
                    percent = int(((i + 1) / len(video_files)) * 100)
                    video_container.button(f"Обработка видео... {percent}%", disabled=True, key=f"btn_v_proc_{i}")
                    v_data = process_single_video(f, logo_h_img, logo_v_img, tw, th, logo_scale)
                    if v_data:
                        zip_file.writestr(os.path.basename(f), v_data)
            st.session_state.video_zip_ready = v_zip_buffer.getvalue()
            st.session_state.video_processing = False
            st.rerun()
        else:
            if video_container.button(f"Создать видео контент {res_text}", type="primary", key="run_video_gen"):
                st.session_state.video_processing = True
                st.session_state.processing = False # Отключаем фото, если нажали видео
                st.rerun()

# Подпись под кнопкой
st.markdown(f'<div class="version-text">Версия 0.0.81. Обновление контента от {yesterday_date}</div>', unsafe_allow_html=True)
