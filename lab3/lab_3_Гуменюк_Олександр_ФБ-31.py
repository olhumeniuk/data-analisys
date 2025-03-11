import os
import glob
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Функція зчитування та обробки CSV-файлів з папки "data"
def build_dataframe(folder):
    files = glob.glob(os.path.join(folder, "*.csv"))
    if not files:
        st.error(f"Не знайдено CSV файлів у папці '{folder}'.")
        return pd.DataFrame()
    
    columns = ['Year', 'Week', 'SMN', 'SMT', 'VCI', 'TCI', 'VHI', 'unused']
    dataframes = []
    
    for file in files:
        try:
            reg_code = int(file.split('__')[1])
        except Exception as e:
            st.write(f"Не вдалося витягти код регіону з файлу {file}: {e}")
            continue
        
        try:
            df = pd.read_csv(file, header=1, names=columns, on_bad_lines='skip')
        except Exception as e:
            st.write(f"Помилка зчитування файлу {file}: {e}")
            continue
        
        try:
            df.at[0, 'Year'] = df.at[0, 'Year'][9:]
        except Exception as e:
            st.write(f"Не вдалося обробити 'Year' у файлі {file}: {e}")
        
        if not df.empty:
            df = df.drop(df.index[-1])  
            df = df[df['VHI'] != -1]     
        df = df.drop(columns=['unused'], errors='ignore')
        
        df.insert(0, 'region_code', reg_code)
        df['Week'] = df['Week'].astype(int)
        
        try:
            df['Year'] = df['Year'].astype(int)
        except Exception as e:
            st.write(f"Не вдалося перетворити 'Year' у числовий тип у файлі {file}: {e}")
        
        dataframes.append(df)
    
    if not dataframes:
        st.error("Не вдалося зчитати жодного файлу.")
        return pd.DataFrame()
    
    full_df = pd.concat(dataframes).drop_duplicates().reset_index(drop=True)
    
    full_df = full_df[(full_df['region_code'] != 12) & (full_df['region_code'] != 20)]
    
    remap = {
        1:22, 2:24, 3:23, 4:25, 5:3, 6:4, 7:8, 8:19, 9:20, 10:21,
        11:9, 13:10, 14:11, 15:12, 16:13, 17:14, 18:15, 19:16, 21:17,
        22:18, 23:6, 24:1, 25:2, 26:6, 27:5
    }
    full_df = full_df.replace({'region_code': remap})
    
    return full_df

# Завантаження даних у DataFrame
df_main = build_dataframe("data")
if df_main.empty:
    st.error("DataFrame порожній. Перевірте наявність коректних CSV файлів у папці 'data'.")
    st.stop()

area_names = {
    1: "Вінницька", 2: "Волинська", 3: "Дніпропетровська", 4: "Донецька",
    5: "Житомирська", 6: "Закарпатська", 7: "Запорізька", 8: "Івано-Франківська",
    9: "Київська", 10: "Кіровоградська", 11: "Луганська", 12: "Львівська",
    13: "Миколаївська", 14: "Одеська", 15: "Полтавська", 16: "Рівненська",
    17: "Сумська", 18: "Тернопільська", 19: "Харківська", 20: "Херсонська",
    21: "Хмельницька", 22: "Черкаська", 23: "Чернівецька", 24: "Чернігівська",
    25: "Республіка Крим"
}

def reset_filters():
    st.session_state.selected_series = "VCI"
    st.session_state.selected_area = "Вінницька"
    st.session_state.week_range = (1, 52)
    st.session_state.year_range = (2000, 2024)
    st.session_state.ascending_order = False
    st.session_state.descending_order = False

if "selected_series" not in st.session_state:
    st.session_state.selected_series = "VCI"
if "selected_area" not in st.session_state:
    st.session_state.selected_area = "Вінницька"
if "week_range" not in st.session_state:
    st.session_state.week_range = (1, 52)
if "year_range" not in st.session_state:
    st.session_state.year_range = (2000, 2024)
if "ascending_order" not in st.session_state:
    st.session_state.ascending_order = False
if "descending_order" not in st.session_state:
    st.session_state.descending_order = False

st.sidebar.header("Панель фільтрів")

st.session_state.selected_series = st.sidebar.selectbox(
    "Оберіть часовий ряд",
    options=["VCI", "TCI", "VHI"],
    index=["VCI", "TCI", "VHI"].index(st.session_state.selected_series)
)

st.session_state.selected_area = st.sidebar.selectbox(
    "Оберіть область",
    options=list(area_names.values()),
    index=list(area_names.values()).index(st.session_state.selected_area)
)

st.session_state.week_range = st.sidebar.slider(
    "Виберіть інтервал тижнів",
    min_value=1,
    max_value=52,
    value=st.session_state.week_range
)

st.session_state.year_range = st.sidebar.slider(
    "Виберіть інтервал років",
    min_value=1981,
    max_value=2024,
    value=st.session_state.year_range
)

ascending_order = st.sidebar.checkbox(
    "Сортувати за зростанням",
    value=st.session_state.ascending_order,
    key="ascending_order"
)

descending_order = st.sidebar.checkbox(
    "Сортувати за спаданням",
    value=st.session_state.descending_order,
    key="descending_order"
)

if ascending_order and descending_order:
    st.sidebar.warning("Увімкнено обидва варіанти сортування. Буде використано сортування за зростанням.")
    descending_order = False

if st.sidebar.button("Скинути фільтри"):
    reset_filters()

col1, col2 = st.columns([1, 2])

with col2:
    tab1, tab2, tab3 = st.tabs(["Таблиця даних", "Графік часових рядів", "Порівняння областей"])
    
    df_filtered = df_main[
        (df_main["Year"] >= st.session_state.year_range[0]) &
        (df_main["Year"] <= st.session_state.year_range[1]) &
        (df_main["Week"] >= st.session_state.week_range[0]) &
        (df_main["Week"] <= st.session_state.week_range[1])
    ]
    
    # Сортування за вибраним часовим рядом
    sort_col = st.session_state.selected_series
    if ascending_order:
        df_filtered = df_filtered.sort_values(by=sort_col, ascending=True)
    elif descending_order:
        df_filtered = df_filtered.sort_values(by=sort_col, ascending=False)
    
    with tab1:
        st.dataframe(df_filtered)
    
    with tab2:
        # Фільтруємо дані для обраної області
        region_key = None
        for key, name in area_names.items():
            if name == st.session_state.selected_area:
                region_key = key
                break
        if region_key is not None:
            area_df = df_filtered[df_filtered["region_code"] == region_key]
            if area_df.empty:
                st.write("Немає даних для обраної області за вказаний інтервал.")
            else:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(area_df["Year"], area_df[sort_col], marker="o")
                ax.set_title(f"{sort_col} для області {st.session_state.selected_area}")
                ax.set_xlabel("Рік")
                ax.set_ylabel(sort_col)
                st.pyplot(fig)
        else:
            st.write("Обрану область не знайдено.")
    
    with tab3:
        # Побудова графіка порівняння – середнє значення обраного показника для кожної області
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        comparison = df_filtered.groupby("region_code")[sort_col].mean().reset_index()
        comparison["Область"] = comparison["region_code"].apply(lambda x: area_names.get(x, f"Регіон {x}"))
        ax2.bar(comparison["Область"], comparison[sort_col])
        ax2.set_title(f"Середнє значення {sort_col} за областями")
        ax2.set_xlabel("Область")
        ax2.set_ylabel(f"Середнє {sort_col}")
        plt.xticks(rotation=45)
        st.pyplot(fig2)
