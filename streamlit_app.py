import streamlit as st

st.set_page_config(
    page_title="EAF ↔ TextGrid Converter",
    page_icon="🔄",
    layout="wide",
)

st.title("EAF ↔ TextGrid Converter ")
st.markdown(
    """
# EAF ↔ TextGrid Streamlit App

Двусторонний конвертер **ELAN (.eaf/.xml)** ⇄ **Praat (.TextGrid)**, который позволяет легко и без потерь преобразовывать разметку речи между форматами.

**Кратко о проекте**  
- В пакете `converters` находится «ядро» конвертеров и тонкие обёртки для выбора видов файлов и обработки ошибок.  
- В папке `pages` реализован интерфейс Streamlit: отдельная вкладка для конвертации EAF → TextGrid и отдельная вкладка для TextGrid → EAF.  
- Файл `streamlit_app.py` служит точкой входа: здесь описание, навигация и ссылка на полную документацию.

**Особенности**  
- Поддержка short- и long-форматов TextGrid.  
- Информативная обработка ошибок с уведомлениями и разворачиваемым трасс-беком.  
- Запуск локально и на Streamlit Community Cloud одним кликом.

Все детали по установке, структуре и примеры использования — в репозитории на GitHub:  
👉 [ConverterProject на GitHub](https://github.com/ulcorn/ConverterProject)

Проект разработан Корниловой Ульяной и Литвиновой Екатериной.
"""
)
