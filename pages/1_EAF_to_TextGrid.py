import tempfile
from pathlib import Path

import streamlit as st

from converters.eaf_to_textgrid_wrap import convert as eaf2tg

st.header("Конвертер EAF → TextGrid")

uploaded = st.file_uploader("Загрузите *.eaf (или *.xml) файл", type=["eaf", "xml"])
mode = st.radio("Выберите формат выходного TextGrid", ["short", "long"], index=0, horizontal=True)

if uploaded is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / uploaded.name
        inp.write_bytes(uploaded.getbuffer())

        out = inp.with_suffix(".TextGrid")

        with st.spinner("Конвертация…"):
            eaf2tg(inp, out, mode=mode)

        st.success("Готово!")
        st.download_button(
            label="📥 Скачать TextGrid",
            data=out.read_bytes(),
            file_name=out.name,
            mime="text/plain",
        )
