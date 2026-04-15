import streamlit as st

# Настройка страницы
st.set_page_config(page_title="Eltex Discount Portal", page_icon="🏢", layout="centered")

# Кастомный CSS для "серьезного" вида
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stApp { border: 4px solid #00599d; border-radius: 15px; padding: 20px; }
    .eltex-header { color: #00599d; text-align: center; font-family: 'Arial Black', sans-serif; text-transform: uppercase; border-bottom: 2px solid #00599d; padding-bottom: 10px; }
    .step-counter { font-weight: bold; color: #666; text-align: center; margin-top: 20px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #00599d; color: white; }
    </style>
    """, unsafe_allow_html=True)

# Инициализация состояния
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'answers' not in st.session_state:
    st.session_state.answers = {}

# --- ЛОГОТИП ---
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("https://eltex-co.ru/upload/medialibrary/72b/72b535d50699042f883659424e0b021d.png")

st.markdown("<h1 class='eltex-header'>Расчет скидки на оборудование</h1>", unsafe_allow_html=True)
st.write("")

# --- БАЗА ДАННЫХ ВОПРОСОВ ---
# 1-10: Личные данные
# 11-19: Твои ссылки на модели
# 20-55: Абсурд

def next_step():
    st.session_state.step += 1

total_steps = 55

# ЛОГИКА ШАГОВ
if st.session_state.step == 1:
    st.subheader("Вопрос №1: Ваше имя")
    st.text_input("Введите имя полностью", key="name", placeholder="Иван")
    st.button("Далее", on_click=next_step)

elif st.session_state.step == 2:
    st.subheader("Вопрос №2: Фамилия")
    st.text_input("Введите фамилию", key="surname")
    st.button("Далее", on_click=next_step)

elif st.session_state.step == 3:
    st.subheader("Вопрос №3: Отчество")
    st.text_input("При наличии", key="patronymic")
    st.button("Далее", on_click=next_step)

elif st.session_state.step == 4:
    st.subheader("Вопрос №4: Паспортные данные")
    st.text_input("Серия и номер", placeholder="0000 000000")
    st.info("Данные необходимы для формирования именного сертификата на скидку")
    st.button("Далее", on_click=next_step)

# --- ТЕХНИЧЕСКИЙ БЛОК (ТВОИ ССЫЛКИ) ---
elif st.session_state.step == 11:
    st.warning("ВНИМАНИЕ: Проверка квалификации инженера")
    st.subheader("Вопрос №11: Какая модель изображена на фото?")
    st.image("https://api.prod.eltex-co.ru/storage/catalog/goods/19/MES1428_front.png")
    options = ["MES1424", "MES1428", "MES1124M", "MES1448B"]
    st.radio("Выберите вариант:", options, key="q11")
    st.button("Подтвердить модель", on_click=next_step)

elif st.session_state.step == 12:
    st.subheader("Вопрос №12: Идентифицируйте устройство Eltex Cloud-ready")
    st.image("https://api.prod.eltex-co.ru/storage/catalog/goods/115/MES1124M_front.png")
    options = ["MES1428", "MES1124", "MES1124M", "ESR-100"]
    st.radio("Выберите вариант:", options, key="q12")
    st.button("Подтвердить модель", on_click=next_step)

elif st.session_state.step == 13:
    st.subheader("Вопрос №13: Выберите верный номенклатурный номер")
    st.image("https://api.prod.eltex-co.ru/storage/catalog/goods/533/MES2300-08_front2.png")
    options = ["MES2408", "MES2300-08", "MES2300-08P", "MES1408"]
    st.radio("Выберите вариант:", options, key="q13")
    st.button("Подтвердить модель", on_click=next_step)

elif st.session_state.step == 14:
    st.subheader("Вопрос №14: Модель устройства на фото?")
    st.image("https://api.prod.eltex-co.ru/storage/catalog/goods/197/MES2408_front.png")
    options = ["MES2408B", "MES2408C", "MES2408", "MES1428"]
    st.radio("Выберите вариант:", options, key="q14")
    st.button("Подтвердить модель", on_click=next_step)

# --- ПЕРЕХОД В АБСУРД ---
elif st.session_state.step == 30:
    st.subheader("Вопрос №30: Психологическая совместимость")
    st.select_slider("Оцените вашу любовь к синему цвету корпуса Eltex:", 
                     options=["Равнодушен", "Приятный", "Обожаю", "Сплю в синей пижаме"])
    st.button("Далее", on_click=next_step)

elif st.session_state.step == 50:
    st.subheader("Вопрос №50: Финальная проверка")
    st.text_input("Кличка вашей первой домашней улитки (для шифрования ключа скидки)")
    st.button("Далее", on_click=next_step)

# --- ЗАГЛУШКА ДЛЯ ПРОПУЩЕННЫХ ШАГОВ ---
elif st.session_state.step < total_steps:
    st.subheader(f"Вопрос №{st.session_state.step}")
    questions_list = {
        5: "Ваш точный рост в мм?",
        6: "Ваш вес при последнем взвешивании?",
        7: "Дата и месяц рождения?",
        15: "Умеете ли вы обжимать витую пару в темноте?",
        20: "Ваш любимый протокол маршрутизации?",
    }
    q_text = questions_list.get(st.session_state.step, "Введите дополнительные данные для уточнения скидки:")
    st.text_input(q_text)
    st.button("Далее", on_click=next_step)

# --- ФИНАЛ ---
else:
    st.balloons()
    st.success("АНКЕТА ЗАВЕРШЕНА!")
    st.subheader("Ваш результат:")
    st.write(f"Поздравляем, **{st.session_state.get('name', 'Пользователь')}**!")
    st.write("На основании ваших ответов и верификации моделей, ваша персональная скидка составила:")
    st.title("0.003%")
    st.info("Скидка действительна только при покупке от 5000 единиц MES1428 и личной подписи директора завода.")
    if st.button("Начать заново"):
        st.session_state.step = 1
        st.rerun()

# Счетчик внизу
st.markdown(f"<p class='step-counter'>Вопрос {st.session_state.step} из {total_steps}</p>", unsafe_allow_html=True)
st.progress(st.session_state.step / total_steps)
