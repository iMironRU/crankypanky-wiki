# CrankyPanky — база знаний для семей с СД1

![License: CC BY-SA 4.0](https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg)
![Статус: скелет](https://img.shields.io/badge/Статус-скелет-yellow)
![Язык: русский](https://img.shields.io/badge/Язык-русский-blue)

Открытый информационно-образовательный ресурс для детей с сахарным диабетом
1 типа и их родителей. Цель — актуальная, применимая в жизни информация.

> **Это обучающий ресурс, а не источник персональных медицинских назначений.**
> Решения по лечению принимаются с лечащим врачом.

## Состояние

Скелет. Инфраструктура (валидатор-гейт, ИИ-предфильтр, расчёт свежести, CI)
готова; контент — заглушки по модулям/параграфам плюс два проработанных
примера: `03-03_libre_predely_krajnie_sluchai` (knowledge) и
`04-02_vybor_pompy_petlya` (decision).

## Локально

```bash
pip install pyyaml python-dateutil mkdocs-material
python tools/validate_metadata.py content/   # гейт доверия
python tools/inject_frontmatter.py            # собрать build/
mkdocs serve                                  # сайт
./scripts/status.sh                           # дашборд свежести
```

Подробности и правила — в [CLAUDE.md](./CLAUDE.md) и
[CONTRIBUTING.md](./CONTRIBUTING.md).
