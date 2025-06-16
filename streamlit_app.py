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
**ELAN.eaf** и **Praat TextGrid** (short/long) без изменения исходных файлов‑конвертеров.
Выберите нужную страницу через боковое меню.
"""
)

st.sidebar.page_link("streamlit_app.py", label="О проекте", icon="ℹ️")
st.sidebar.page_link("pages/1_EAF_to_TextGrid.py", label="EAF → TextGrid", icon="➡️")
st.sidebar.page_link("pages/2_TextGrid_to_EAF.py", label="TextGrid → EAF", icon="⬅️")
