import traceback
import tempfile
from pathlib import Path

import streamlit as st
from converters.eaf_to_textgrid_wrap import convert as eaf2tg
from converters import ConversionError

st.header("Конвертер EAF → TextGrid")

file = st.file_uploader("Загрузите .eaf", type=["eaf", "xml"])
mode = st.radio("Формат TextGrid:", ["short", "long"], horizontal=True)

if file:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / file.name
        src.write_bytes(file.getbuffer())
        dst = src.with_suffix(".TextGrid")

        with st.spinner("Конвертация…"):
            try:
                eaf2tg(src, dst, mode=mode)
            except ConversionError as err:
                st.error(f"❌ {err}")

                with st.expander("Показать подробности"):
                    st.code(traceback.format_exc())
                st.stop()

        st.success("✅ Готово!")
        st.download_button("📥 Скачать", dst.read_bytes(), file_name=dst.name)
