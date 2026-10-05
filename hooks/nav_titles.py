"""MkDocs-хук: разделы навигации называются по заголовку модуля, а не по папке.

Без него MkDocs берёт имя раздела из каталога («00 doverie»), а страница
модуля (_module.md) висит последней в разделе. Хук берёт заголовок из первой
строки «# N. Название» файла _module.md, ставит его разделу и переносит
страницу модуля первой (её оглавление собирает tools/inject_frontmatter.py).
"""
import re


def on_nav(nav, config, files):
    for section in nav.items:
        if not section.is_section:
            continue
        module = next((c for c in section.children
                       if c.is_page and c.file.src_uri.endswith("/_module.md")), None)
        if module is None:
            continue
        with open(module.file.abs_src_path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"#\s+(.+)", line)
                if m:
                    section.title = m.group(1).strip()
                    break
        section.children.remove(module)
        section.children.insert(0, module)
    return nav
