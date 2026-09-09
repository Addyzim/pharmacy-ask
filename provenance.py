# -*- coding: utf-8 -*-
"""Происхождение данных: таблица -> исходный файл, лист, что означает.

Используется, чтобы под каждым ответом показать, откуда взяты цифры.
"""

SOURCES = {
    "arrivals":     {"file": "Arrivals.XLSX",     "sheet": "TDSheet", "system": "1С: Поступление товаров",
                     "title": "Приходы от поставщиков"},
    "check_lines":  {"file": "CheckUASNew.XLSX",  "sheet": "TDSheet", "system": "ККМ / УАС, строки чеков",
                     "title": "Строки чеков (детализация)"},
    "cheques":      {"file": "ChequesWeeklyNew.XLSX", "sheet": "TDSheet", "system": "ККМ, шапки чеков",
                     "title": "Чеки (шапки)"},
    "refusals":     {"file": "Refusals.XLSX",     "sheet": "TDSheet", "system": "1С: Отказы покупателям",
                     "title": "Отказы (дефектура)"},
    "so_days":      {"file": "SO days.xlsx",      "sheet": "TDSheet", "system": "1С: Остатки на дату среза",
                     "title": "Остатки для SO days"},
    "sales_online": {"file": "SalesOnline.XLSX",  "sheet": "TDSheet", "system": "Интернет-магазин",
                     "title": "Онлайн-заказы"},
    "sales_weekly": {"file": "SalesWeekly.XLSX",  "sheet": "TDSheet", "system": "1С: Реализация товаров",
                     "title": "Продажи по позициям"},
    "stock":        {"file": "Stock.XLSX",        "sheet": "TDSheet", "system": "1С: Остатки по дням",
                     "title": "Остатки на складах"},
    "movements":    {"file": "Движения товаров с ценами. Номенклатура серия (XLSX).xlsx",
                     "sheet": "TDSheet + TDSheet1", "system": "1С: Движения по сериям",
                     "title": "Движение товара и цены по сериям"},
    "sales_4m":     {"file": "Продажи 4 мес справочник.xlsx", "sheet": "TDSheet",
                     "system": "1С: Продажи за 4 месяца", "title": "Продажи за 4 месяца"},
    "products":     {"file": "Справочник номенклатур.xlsx", "sheet": "TDSheet",
                     "system": "1С: Справочник номенклатуры", "title": "Справочник номенклатуры"},
    "stores":       {"file": "Цель на Мес.xlsx",  "sheet": "Районы", "system": "Мастер-данные сети",
                     "title": "Справочник аптек"},
    "targets":      {"file": "Цель на Мес.xlsx",  "sheet": "Таргет", "system": "План продаж",
                     "title": "Планы на месяц и неделю"},
}

# Формулы метрик — показываем пользователю, как именно посчитано.
FORMULAS = {
    "выручка": "Выручка = SUM(СуммаСоСкидкой) по sales_weekly",
    "средний чек": "Средний чек = SUM(Сумма) / COUNT(чеков) по cheques, только Вид_операции='Продажа'",
    "глубина": "Глубина чека = SUM(Количество) / COUNT(DISTINCT Номер) по check_lines",
    "маржа": "Маржа % = (Выручка − СебестоимостьПродаж) / Выручка × 100 по check_lines",
    "план": "Выполнение % = Факт выручки / targets.Недельный_таргет × 100",
    "отказ": "Отказы = SUM(Количество) по refusals — упущенный спрос",
    "остат": "Товарный запас = SUM(Сумма_остатка) по stock на MAX(Дата)",
}


def tables_in_sql(sql: str):
    """Какие таблицы реально участвовали в запросе."""
    low = sql.lower()
    return [t for t in SOURCES if t in low]


def describe(tables, row_counts):
    out = []
    for t in tables:
        s = SOURCES.get(t, {})
        out.append({
            "table": t,
            "title": s.get("title", t),
            "file": s.get("file", "—"),
            "sheet": s.get("sheet", "—"),
            "system": s.get("system", "—"),
            "rows": row_counts.get(t, 0),
        })
    return out
