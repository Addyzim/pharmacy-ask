# -*- coding: utf-8 -*-
"""Сборка статической версии для GitHub Pages: docs/.

Витрина уезжает в браузер целиком (sql.js), поэтому сервер не нужен.
Запуск: python build_static.py
"""
import json
import os
import shutil
import sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(BASE, "docs")
DB = os.path.join(BASE, "pharmacy.db")


def main():
    from app import INSIGHT, SYSTEM          # единый источник промптов
    from demo_questions import DEMO
    from provenance import SOURCES

    os.makedirs(DOCS, exist_ok=True)

    # витрина и выгрузки — их же отдаём на скачивание из интерфейса
    shutil.copy(DB, os.path.join(DOCS, "pharmacy.db"))
    for sub in ("data", "sql"):
        dst = os.path.join(DOCS, sub)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(BASE, sub), dst)

    # готовые вопросы
    with open(os.path.join(DOCS, "questions.json"), "w", encoding="utf-8") as f:
        json.dump([{"q": d["q"], "keys": d["keys"], "plan": d["plan"]} for d in DEMO],
                  f, ensure_ascii=False, indent=1)

    # происхождение данных + количество строк
    con = sqlite3.connect(DB)
    counts = {t: con.execute(f"select count(*) from {t}").fetchone()[0]
              for (t,) in con.execute("select name from sqlite_master where type='table'")}
    con.close()
    src = {t: dict(m, rows=counts.get(t, 0),
                   size_kb=round(os.path.getsize(os.path.join(BASE, "data", m["file"])) / 1024))
           for t, m in SOURCES.items()}
    with open(os.path.join(DOCS, "sources.json"), "w", encoding="utf-8") as f:
        json.dump(src, f, ensure_ascii=False, indent=1)

    # каталог конструктора таблиц
    import model
    with open(os.path.join(DOCS, "model.json"), "w", encoding="utf-8") as f:
        json.dump(model.catalog(), f, ensure_ascii=False)

    # промпты для режима с ключом
    with open(os.path.join(DOCS, "prompts.json"), "w", encoding="utf-8") as f:
        json.dump({"system": SYSTEM, "insight": INSIGHT}, f, ensure_ascii=False)

    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    total = sum(os.path.getsize(os.path.join(r, n))
                for r, _, fs in os.walk(DOCS) for n in fs)
    print(f"docs/ собран: {len(DEMO)} вопросов, {len(src)} источников, "
          f"{round(total / 1024 / 1024, 1)} МБ")


if __name__ == "__main__":
    main()
