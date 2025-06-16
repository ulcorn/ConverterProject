import tempfile
from pathlib import Path

import streamlit as st

from converters.textgrid_to_eaf_wrap import convert as tg2eaf

st.header("Конвертер TextGrid → EAF")

uploaded = st.file_uploader(
    "Загрузите *.TextGrid (или *.textgrid) файл",
    type=["TextGrid", "textgrid", "tg"],
)
mode = st.radio(
    "Формат вашего TextGrid‑файла",
    ["short", "long"],
    index=0,
    horizontal=True,
    help="Нужно лишь для информации – конвертер определяет тип автоматически.",
)

if uploaded is not None:
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = Path(tmpdir) / uploaded.name
        inp.write_bytes(uploaded.getbuffer())

        out = inp.with_suffix(".eaf")

        with st.spinner("Конвертация…"):
            tg2eaf(inp, out, mode=mode)

        st.success("Готово!")
        st.download_button(
            label="📥 Скачать EAF",
            data=out.read_bytes(),
            file_name=out.name,
            mime="application/xml",
        )
