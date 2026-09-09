# -*- coding: utf-8 -*-
"""Семантический слой витрины: что с чем можно считать.

Каждая метрика живёт в своей таблице фактов, каждое измерение требует от таблицы
определённого ключа (аптека, товар, дата) или собственной колонки. Отсюда система
знает, какие пары метрика-измерение осмысленны, а о каких надо предупредить.
"""

# ── таблицы фактов: какие ключи есть и какие собственные разрезы
FACTS = {
    "sales_weekly": {
        "title": "Продажи по позициям",
        "keys": {"store": "Магазин", "product": "Номенклатура", "date": "Дата"},
        "own": {"group": "Группа", "rx": "Рецептурный", "pharm": "ФармГруппа"},
    },
    "check_lines": {
        "title": "Строки чеков",
        "keys": {"store": "Магазин", "product": "Номенклатура", "date": "Дата"},
        "own": {"seller": "Продавец", "gender": "Пол", "optype": "ВидОперации"},
        "where": "check_lines.ВидОперации = 'Продажа'",
    },
    "cheques": {
        "title": "Чеки",
        "keys": {"store": "Магазин", "date": "Дата"},
        "own": {"optype": "Вид_операции"},
        "where": "cheques.Вид_операции = 'Продажа'",
    },
    "stock": {
        "title": "Остатки",
        "keys": {"store": "Склад", "product": "Номенклатура", "date": "Дата"},
        "own": {"group": "Группа"},
        "where": "stock.Дата = (SELECT MAX(Дата) FROM stock)",
    },
    "refusals": {
        "title": "Отказы",
        "keys": {"store": "Магазин", "product": "Товар", "date": "Дата"},
        "own": {"group": "Группа"},
    },
    "sales_online": {
        "title": "Онлайн-заказы",
        "keys": {"product": "Номенклатура", "date": "Дата"},
        "own": {"group": "Группа", "status": "Статус"},
        "where": "sales_online.Статус <> 'Отменён'",
    },
    "arrivals": {
        "title": "Приходы от поставщиков",
        "keys": {"store": "Склад", "date": "Дата"},
        "own": {"partner": "Партнер"},
    },
    "movements": {
        "title": "Движения по сериям",
        "keys": {"store": "Склад", "product": "Номенклатура"},
        "own": {"group": "Группа"},
    },
    "sales_4m": {
        "title": "Продажи за 4 месяца",
        "keys": {"store": "Магазин", "product": "Номенклатура", "date": "Дата"},
        "own": {"group": "Группа", "supplier": "Поставщик", "rx": "Рецептурный"},
    },
}

WEEKDAY = ("CASE strftime('%w', {date}) WHEN '0' THEN 'Вс' WHEN '1' THEN 'Пн' "
           "WHEN '2' THEN 'Вт' WHEN '3' THEN 'Ср' WHEN '4' THEN 'Чт' "
           "WHEN '5' THEN 'Пт' ELSE 'Сб' END")

# ── измерения: need — что требуется от таблицы фактов
DIMS = [
    {"id": "store", "title": "Аптека", "alias": "Аптека", "need": "store",
     "expr": "{store}"},
    {"id": "district", "title": "Район", "alias": "Район", "need": "store",
     "join": "stores", "expr": "stores.Район"},
    {"id": "product", "title": "Номенклатура", "alias": "Номенклатура", "need": "product",
     "expr": "{product}"},
    {"id": "manufacturer", "title": "Производитель", "alias": "Производитель",
     "need": "product", "join": "products", "expr": "products.Производитель"},
    {"id": "pharm_group", "title": "Фарм-группа", "alias": "Фарм_группа",
     "need": "product", "join": "products", "expr": "products.Фарм_группа"},
    {"id": "rx", "title": "Рецептурный", "alias": "Рецептурный",
     "need": "product", "join": "products", "expr": "products.Рецептурный"},
    {"id": "group", "title": "Товарная группа", "alias": "Товарная_группа",
     "need": "own:group", "expr": "{own}"},
    {"id": "day", "title": "День", "alias": "День", "need": "date",
     "expr": "substr({date}, 1, 10)"},
    {"id": "month", "title": "Месяц", "alias": "Месяц", "need": "date",
     "expr": "substr({date}, 1, 7)"},
    {"id": "weekday", "title": "День недели", "alias": "День_недели", "need": "date",
     "expr": WEEKDAY},
    {"id": "seller", "title": "Продавец", "alias": "Продавец", "need": "own:seller",
     "expr": "{own}"},
    {"id": "gender", "title": "Пол покупателя", "alias": "Пол", "need": "own:gender",
     "expr": "{own}"},
    {"id": "partner", "title": "Поставщик прихода", "alias": "Поставщик",
     "need": "own:partner", "expr": "{own}"},
    {"id": "supplier", "title": "Поставщик товара", "alias": "Поставщик_товара",
     "need": "own:supplier", "expr": "{own}"},
    {"id": "status", "title": "Статус заказа", "alias": "Статус", "need": "own:status",
     "expr": "{own}"},
]

# ── метрики: agg — готовое выражение, formula — как объясняем человеку
METRICS = [
    {"id": "revenue", "title": "Выручка", "alias": "Выручка", "fact": "sales_weekly",
     "agg": "ROUND(SUM(sales_weekly.СуммаСоСкидкой))",
     "formula": "Выручка = SUM(СуммаСоСкидкой) по sales_weekly"},
    {"id": "revenue_gross", "title": "Выручка без скидки", "alias": "Выручка_без_скидки",
     "fact": "sales_weekly", "agg": "ROUND(SUM(sales_weekly.СуммаБезСкидки))",
     "formula": "Выручка без скидки = SUM(СуммаБезСкидки)"},
    {"id": "discount", "title": "Скидка", "alias": "Скидка", "fact": "sales_weekly",
     "agg": "ROUND(SUM(sales_weekly.СуммаБезСкидки) - SUM(sales_weekly.СуммаСоСкидкой))",
     "formula": "Скидка = SUM(СуммаБезСкидки) − SUM(СуммаСоСкидкой)"},
    {"id": "qty", "title": "Продано штук", "alias": "Штук", "fact": "sales_weekly",
     "agg": "SUM(sales_weekly.Количество)", "formula": "Штук = SUM(Количество)"},
    {"id": "checks", "title": "Чеков", "alias": "Чеков", "fact": "cheques",
     "agg": "COUNT(*)", "formula": "Чеков = COUNT(*) по продажным чекам"},
    {"id": "avg_check", "title": "Средний чек", "alias": "Средний_чек", "fact": "cheques",
     "agg": "ROUND(SUM(cheques.Сумма) / COUNT(*))",
     "formula": "Средний чек = SUM(Сумма) / COUNT(чеков)"},
    {"id": "depth", "title": "Глубина чека", "alias": "Глубина_чека", "fact": "check_lines",
     "agg": "ROUND(1.0 * SUM(check_lines.Количество) / COUNT(DISTINCT check_lines.Номер), 2)",
     "formula": "Глубина = SUM(Количество) / COUNT(DISTINCT Номер)"},
    {"id": "margin", "title": "Маржа, %", "alias": "Маржа_проц", "fact": "check_lines",
     "agg": ("ROUND(100.0 * (SUM(check_lines.Выручка) - SUM(check_lines.СебестоимостьПродаж))"
             " / SUM(check_lines.Выручка), 1)"),
     "formula": "Маржа % = (Выручка − Себестоимость) / Выручка × 100"},
    {"id": "cogs", "title": "Себестоимость", "alias": "Себестоимость", "fact": "check_lines",
     "agg": "ROUND(SUM(check_lines.СебестоимостьПродаж))",
     "formula": "Себестоимость = SUM(СебестоимостьПродаж)"},
    {"id": "stock_sum", "title": "Остаток, сумма", "alias": "Остаток_сумма", "fact": "stock",
     "agg": "ROUND(SUM(stock.Сумма_остатка))",
     "formula": "Запас = SUM(Сумма_остатка) на последнюю дату среза"},
    {"id": "stock_qty", "title": "Остаток, штук", "alias": "Остаток_штук", "fact": "stock",
     "agg": "SUM(stock.Количество_остаток)",
     "formula": "Остаток штук = SUM(Количество_остаток) на последнюю дату"},
    {"id": "refusals", "title": "Отказы, штук", "alias": "Отказов", "fact": "refusals",
     "agg": "SUM(refusals.Количество)", "formula": "Отказы = SUM(Количество) по refusals"},
    {"id": "online_revenue", "title": "Онлайн-выручка", "alias": "Онлайн_выручка",
     "fact": "sales_online", "agg": "ROUND(SUM(sales_online.Сумма_с_НДС))",
     "formula": "Онлайн = SUM(Сумма_с_НДС) по неотменённым заказам"},
    {"id": "online_profit", "title": "Онлайн, валовая прибыль", "alias": "Валовая_прибыль",
     "fact": "sales_online", "agg": "ROUND(SUM(sales_online.Валовая_прибыль))",
     "formula": "Валовая прибыль = SUM(Валовая_прибыль)"},
    {"id": "arrivals_sum", "title": "Приход, сумма", "alias": "Приход_сумма", "fact": "arrivals",
     "agg": "ROUND(SUM(arrivals.Сумма))", "formula": "Приход = SUM(Сумма) по arrivals"},
    {"id": "markup", "title": "Наценка, %", "alias": "Наценка_проц", "fact": "movements",
     "agg": "ROUND(AVG(movements.Наценка_поступления), 1)",
     "formula": "Наценка = AVG(Наценка_поступления) по партиям"},
    {"id": "sales_4m_sum", "title": "Продажи за 4 мес", "alias": "Продажи_4мес", "fact": "sales_4m",
     "agg": "ROUND(SUM(sales_4m.Сумма_продаж_со_скидкой))",
     "formula": "Продажи за 4 месяца = SUM(Сумма продаж со скидкой)"},
]

JOIN_SQL = {
    "stores": "LEFT JOIN stores ON stores.Магазин = {fact}.{store}",
    "products": "LEFT JOIN products ON products.Наименование = {fact}.{product}",
}


def dim_expr(dim, fact):
    """Выражение измерения для конкретной таблицы фактов или None, если несовместимо."""
    meta = FACTS[fact]
    need = dim["need"]
    if need.startswith("own:"):
        col = meta.get("own", {}).get(need[4:])
        if not col:
            return None
        return dim["expr"].replace("{own}", f'{fact}."{col}"')
    key = meta.get("keys", {}).get(need)
    if not key:
        return None
    expr = dim["expr"]
    for k, v in meta.get("keys", {}).items():
        expr = expr.replace("{" + k + "}", f'{fact}."{v}"')
    return expr


def catalog():
    """Каталог для интерфейса: измерения с готовыми выражениями по каждой витрине."""
    dims = []
    for d in DIMS:
        facts = {}
        for f in FACTS:
            e = dim_expr(d, f)
            if e:
                facts[f] = {"expr": e, "join": d.get("join")}
        if facts:
            dims.append({"id": d["id"], "title": d["title"], "alias": d["alias"],
                         "need": d["need"], "facts": facts})

    joins = {}
    for f, meta in FACTS.items():
        keys = meta.get("keys", {})
        j = {}
        if "store" in keys:
            j["stores"] = JOIN_SQL["stores"].format(fact=f, store=f'"{keys["store"]}"')
        if "product" in keys:
            j["products"] = JOIN_SQL["products"].format(fact=f, product=f'"{keys["product"]}"')
        joins[f] = j

    return {
        "facts": {f: {"title": m["title"], "where": m.get("where", "")}
                  for f, m in FACTS.items()},
        "dims": dims,
        "metrics": METRICS,
        "joins": joins,
    }
