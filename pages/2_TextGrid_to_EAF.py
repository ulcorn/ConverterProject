import traceback
import tempfile
from pathlib import Path

import streamlit as st
from converters.textgrid_to_eaf_wrap import convert as tg2eaf
from converters import ConversionError

st.header("Конвертер TextGrid → EAF")

file = st.file_uploader("Загрузите .TextGrid / .tg", type=["TextGrid", "tg"])
mode = st.radio("Какой у файла формат", ["short", "long"], horizontal=True)

if file:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / file.name
        src.write_bytes(file.getbuffer())
        dst = src.with_suffix(".eaf")

        with st.spinner("Конвертация…"):
            try:
                tg2eaf(src, dst, mode=mode)
            except ConversionError as err:
                st.error(f"❌ {err}")
                with st.expander("Детали ошибки"):
                    st.code(traceback.format_exc())
                st.stop()

        st.success("✅ Готово!")
        st.download_button("📥 Скачать EAF", dst.read_bytes(), file_name=dst.name)
