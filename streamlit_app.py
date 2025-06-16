import streamlit as st

st.set_page_config(
    page_title="EAF ↔ TextGrid Converter",
    page_icon="🔄",
    layout="wide",
)

st.title("EAF ↔ TextGrid Converter ")
st.markdown(
    """
Приложение выполняет двустороннюю конвертацию между
**ELAN.eaf** и **Praat TextGrid** (short/long) без изменения исходных файлов.
Выберите нужную страницу через боковое меню.
"""
)