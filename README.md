# EAF↔ TextGrid Streamlit App

Двусторонний конвертер **ELAN(.eaf/.xml)**⇄**Praat(.TextGrid)**  
Работает локально и на Streamlit Community Cloud.

---

## Cтруктура проекта

````
eaf_textgrid_app
│
├─ streamlit_app.py            # главная страница (о проекте)
│
├─ pages                      # две вкладки Streamlit‑мульти‑apps
│   ├─ 1_EAF_to_TextGrid.py    # конвертер EAF → TextGrid
│   └─ 2_TextGrid_to_EAF.py    # конвертер TextGrid → EAF
│
├─ converters                 # логика конвертации
│   ├─ init.py             # ConversionError + экспорт модулей
│   ├─ eaf_to_textgrid_core.py # Основная обработка файлов .eaf
│   ├─ textgrid_to_eaf_core.py # Основная обработка файлов .textgrid
│   ├─ eaf_to_textgrid_wrap.py # обёртка с выбором short/long + try/except
│   └─ textgrid_to_eaf_wrap.py # обёртка + try/except
│
├─ requirements.txt            # зависимости
└─ README.md                   # вы читаете его

````

---

## Установка и запуск локально

```bash
# 1. клонировать репозиторий
git clone https://github.com/ulcorn/eaf_textgrid_app.git
cd eaf_textgrid_app

# 2. создать виртуальное окружение (рекомендуется)
python -m venv .venv
source .venv/bin/activate # Windows: .venv\Scripts\activate

# 3. установить зависимости
pip install -r requirements.txt

# 4. запустить приложение
streamlit run streamlit_app.py
````

Откроется браузер на `http://localhost:8501` c тремя вкладками:

| Вкладка            | Что делает                                                                |
|--------------------|---------------------------------------------------------------------------|
| **О проекте**      | краткая справка и навигация                                               |
| **EAF → TextGrid** | загрузите `.eaf/.xml`, выберите `short`/`long`, скачайте `.TextGrid`      |
| **TextGrid → EAF** | загрузите `.TextGrid`, при желании отметьте `short/long`, скачайте `.eaf` |

## Как устроен код

| Cлой     | Файл(ы)                                              | Ответственность                                                                                                         |
|----------|------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| **Core** | `eaf_to_textgrid_core.py`, `textgrid_to_eaf_core.py` | ‑ собственно конвертация                                                                                                |
| **Wrap** | `eaf_to_textgrid_wrap.py`, `textgrid_to_eaf_wrap.py` | ‑ валидирует аргументы, добавляет выбор `short/long`, перехватывает низкоуровневые ошибки и поднимает `ConversionError` |
| **UI**   | `pages/*.py`                                         | ‑ Streamlit‑интерфейс, ловит `ConversionError`, показывает `st.error` + разворачиваемый трейсбек                        |

`ConversionError` объявлен в`converters/__init__.py` и импортируется обёртками и UI, чтобы ловить все проблемы
единообразно.

---

## Отладка и обработка ошибок

* Внутренние ошибки (`FileNotFoundError`, битый XML и т. д.) схлопываются
  в `ConversionError`.
* На странице Streamlit выводится красное сообщение **“❌ ошибка”** и раскрывающийся блок с полным traceback.

---

## 📝 Прочее

* **При желании можно не создавать локально никаких файлов и сразу перейти по ссылке:**
  
  [Перейти к приложению на Streamlit Cloud](https://converterproject-9caqoxr7qbx6ae22gscb4y.streamlit.app)

* **Short / Long TextGrid**
  * При конвертации *EAF → TextGrid* выбор формата влияет на аргумент `praatio.save(format="…")`. 
  * При *TextGrid → EAF* ядро само определяет формат, переключатель нужен лишь для UI‑единообразия.

* **Совместимость**
  
  Приложение тестировано под Python 3.9–3.12, Streamlit ≥ 1.33, `pympi‐ling`1.71, `praatio`6 .x.

* **Безопасность**
  
  Все файлы обрабатываются во временной директории, в оперативной памяти.
  Ничего не сохраняется на сервер, кроме как отдаётся пользователю через кнопку *Download*.
