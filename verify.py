# -*- coding: utf-8 -*-
"""Анти-галлюцинация: проверяем, что каждое число из текста ответа есть в результате SQL.

Числа, которых нет ни в одной ячейке (и ни в одной очевидной агрегации по ним),
помечаются как непроверенные — интерфейс показывает предупреждение.
"""
import re

NUM = re.compile(r"-?\d[\d\s  ]*(?:[.,]\d+)?")


def _to_float(s: str):
    s = s.replace(" ", "").replace(" ", "").replace(" ", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def candidates(columns, rows):
    """Все значения, которые модель имеет право назвать."""
    vals = set()

    def add(v):
        if v is None:
            return
        vals.add(round(v, 6))
        vals.add(round(v))
        vals.add(round(v, 1))
        vals.add(round(v, 2))
        for d in (1e3, 1e6, 1e9):
            vals.add(round(v / d, 1))
            vals.add(round(v / d, 2))

    numeric_cols = {}
    for r in rows:
        for i, v in enumerate(r):
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)):
                add(float(v))
                numeric_cols.setdefault(i, []).append(float(v))

    add(float(len(rows)))
    for i, col in numeric_cols.items():
        add(sum(col))                      # итог по колонке
        add(sum(col) / len(col))           # среднее
        add(max(col))
        add(min(col))
        s = sorted(col, reverse=True)
        if len(s) > 1:
            add(s[0] - s[1])               # разрыв между лидерами
            if s[1]:
                add(s[0] / s[1])
                add(100.0 * s[0] / s[1])
        total = sum(col)
        if total:
            for v in col:                  # доли в процентах
                add(100.0 * v / total)
    return vals


def check(answer: str, question: str, columns, rows, tol=0.012):
    """Возвращает список чисел из ответа, которых нет в данных."""
    if not rows:
        return []
    allowed = candidates(columns, rows)
    asked = {_to_float(m.group()) for m in NUM.finditer(question)}
    bad = []
    for m in NUM.finditer(answer):
        v = _to_float(m.group())
        if v is None or abs(v) < 10:
            continue
        if 1900 <= v <= 2100 and float(v).is_integer():
            continue                        # год
        if v in asked:
            continue
        ok = any(abs(v - c) <= max(tol * abs(v), 0.05) for c in allowed)
        if not ok:
            bad.append(m.group().strip())
    return sorted(set(bad), key=len, reverse=True)[:5]
