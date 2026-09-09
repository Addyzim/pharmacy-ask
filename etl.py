# -*- coding: utf-8 -*-
"""Excel -> SQLite. Запуск: python etl.py"""
import io, os, re, sqlite3
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
DB = os.path.join(BASE, "pharmacy.db")

# файл -> (лист, имя таблицы)
SOURCES = [
    ("Arrivals.XLSX",            "TDSheet", "arrivals"),
    ("CheckUASNew.XLSX",         "TDSheet", "check_lines"),
    ("ChequesWeeklyNew.XLSX",    "TDSheet", "cheques"),
    ("Refusals.XLSX",            "TDSheet", "refusals"),
    ("SO days.xlsx",             "TDSheet", "so_days"),
    ("SalesOnline.XLSX",         "TDSheet", "sales_online"),
    ("SalesWeekly.XLSX",         "TDSheet", "sales_weekly"),
    ("Stock.XLSX",               "TDSheet", "stock"),
    ("Движения товаров с ценами. Номенклатура серия (XLSX).xlsx", "TDSheet",  "movements"),
    ("Движения товаров с ценами. Номенклатура серия (XLSX).xlsx", "TDSheet1", "movements"),
    ("Продажи 4 мес справочник.xlsx", "TDSheet", "sales_4m"),
    ("Справочник номенклатур.xlsx",   "TDSheet", "products"),
    ("Цель на Мес.xlsx",              "Районы",  "stores"),
    ("Цель на Мес.xlsx",              "Таргет",  "targets"),
]

RENAME = {
    "30.04.2023 0:00:00 Количество начальный остаток": "Количество_начальный_остаток",
    "Характеристика.Номенклатура.Регистратор": "Регистратор",
    "Характеристика.Номенклатура.Рецептурный": "Рецептурный",
    "Характеристика.Номенклатура.Код": "Код",
    "Характеристика.Номенклатура.Входит в группу": "Группа",
    "Характеристика.Поставщик (Доп. свойство)": "Поставщик",
    "Документ продажи.Дата": "Дата",
    "Серия.Дата поступления": "Серия_дата_поступления",
    "Серия.Номер": "Серия_номер",
    "Серия.Годен до": "Серия_годен_до",
    "Сумма c НДС": "Сумма_с_НДС",
    "Количество (в единицах хранения)": "Количество",
}

PREFIX_RENAME = [
    ("30.04", "Количество_начальный_остаток"),
    ("Характеристика.Номенклатура.Регистратор", "Регистратор"),
    ("Характеристика.Номенклатура.Рецептурный", "Рецептурный"),
    ("Характеристика.Номенклатура.Код", "Код"),
    ("Характеристика.Номенклатура.Входит", "Группа"),
    ("Характеристика.Поставщик", "Поставщик"),
]

DROP_COLS = {"F9", "F10", "F11", "F12", "Д Т", "Ссылка"}


def clean(name: str) -> str:
    n = str(name).strip()
    for pref, v in PREFIX_RENAME:
        if n.startswith(pref):
            return v
    n = RENAME.get(n, n)
    n = re.sub(r"[^0-9A-Za-zА-Яа-яЁё]+", "_", n).strip("_")
    if re.match(r"^\d", n):
        n = "c_" + n
    return n

DATE_HINT = re.compile(r"дат|годен", re.I)

def to_iso(s: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(s):
        return s.dt.strftime("%Y-%m-%d %H:%M:%S")
    out = pd.to_datetime(s, format="%d.%m.%Y", errors="coerce")
    if out.notna().sum() >= max(1, int(0.5 * s.notna().sum())):
        return out.dt.strftime("%Y-%m-%d %H:%M:%S")
    return s

def main():
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    loaded = {}
    for fname, sheet, table in SOURCES:
        path = os.path.join(DATA, fname)
        df = pd.read_excel(path, sheet_name=sheet)
        df = df.drop(columns=[c for c in df.columns if str(c).strip() in DROP_COLS], errors="ignore")
        df.columns = [clean(c) for c in df.columns]
        df = df.drop(columns=[c for c in df.columns if c in DROP_COLS], errors="ignore")
        df = df.loc[:, ~df.columns.duplicated()]
        df = df.dropna(axis=1, how="all")
        for c in df.columns:
            if DATE_HINT.search(c):
                df[c] = to_iso(df[c])
        mode = "append" if table in loaded else "replace"
        df.to_sql(table, con, if_exists=mode, index=False)
        loaded[table] = loaded.get(table, 0) + len(df)
        print(f"{table:<14} <- {fname[:38]:<38} [{sheet}] {len(df)} строк")
    con.commit()
    export_sql(con)
    print("\nИтого таблиц:", len(loaded), "| БД:", DB)
    con.close()


def export_sql(con: sqlite3.Connection):
    """Выгрузка витрины в .sql — источник можно отдать заказчику или поднять где угодно."""
    sqldir = os.path.join(BASE, "sql")
    os.makedirs(sqldir, exist_ok=True)
    ddl = [r[0] for r in con.execute(
        "select sql from sqlite_master where type='table' and sql is not null")]
    with io.open(os.path.join(sqldir, "schema.sql"), "w", encoding="utf-8") as f:
        f.write("-- Pharmacy Ask: структура витрины (SQLite)\n\n")
        f.write(";\n\n".join(ddl) + ";\n")
    with io.open(os.path.join(sqldir, "pharmacy_dump.sql"), "w", encoding="utf-8") as f:
        f.write("-- Pharmacy Ask: полная выгрузка данных (SQLite dump)\n")
        for line in con.iterdump():
            f.write(line + "\n")
    print("SQL выгрузка: sql/schema.sql, sql/pharmacy_dump.sql")


if __name__ == "__main__":
    main()
