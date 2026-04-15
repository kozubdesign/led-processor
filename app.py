# ====================== ЖЁСТКИЙ CSS ======================
st.markdown("""
    <style>
    .block-container {
        max-width: 720px !important;
        margin: 0 auto !important;
        padding-top: 2rem !important;
    }

    /* Контейнер для логотипа - центрирование */
    div[data-testid="stImage"] {
        text-align: center !important;
        display: block !important;
    }
    
    div[data-testid="stImage"] img {
        margin: 0 auto 30px auto !important;
        height: 68px;
        width: auto;
        display: block !important;
    }

    h1 {
        text-align: center !important;
        font-size: 2.25rem !important;
        margin-bottom: 12px !important;
    }

    .subtitle {
        text-align: center !important;
        color: #666;
        font-size: 1.05rem;
        margin-bottom: 40px !important;
    }

    .params-title {
        text-align: center !important;
        font-size: 1.35rem;
        margin: 30px 0 22px 0;
    }

    /* Поля ввода по центру */
    div[data-testid="stNumberInput"] {
        margin: 0 auto 16px auto !important;
        max-width: 380px !important;
    }

    /* Кнопка - правильное центрирование */
    .stButton {
        display: flex !important;
        justify-content: center !important;
        width: 100% !important;
        margin: 10px 0 20px 0 !important;
    }
    
    /* Дополнительный обходной путь для центрирования кнопки */
    div[data-testid="column"] .stButton {
        display: flex !important;
        justify-content: center !important;
    }
    
    .stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 1.12rem !important;
        height: 54px !important;
        min-width: 320px !important;
        padding: 0 55px !important;
        border-radius: 8px !important;
        margin: 0 auto !important;
    }
    
    /* Обёртка кнопки */
    .element-container:has(.stButton) {
        display: flex !important;
        justify-content: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================== ЛОГОТИП ======================
is_dark = st.get_option("theme.base") == "dark"
header_logo = LOGO_PATH if is_dark else LOGO_BLACK_PATH

if os.path.exists(header_logo):
    # Используем колонки для центрирования (самый надёжный способ)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(header_logo, width=190)
