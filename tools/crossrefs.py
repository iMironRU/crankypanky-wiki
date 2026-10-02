"""Перекрёстные отсылки «→ См. «Заголовок»». Разбор и разрешение — ТОЛЬКО здесь.
Авторы пишут в content/ простой текст; ссылкой он становится при сборке build/
(inject_frontmatter.py); битую валидатор (validate_metadata.py) показывает
предупреждением, сборку она не валит.

Карточка ищется по title из *.meta.yml, модуль — по заголовку _module.md без
номера («# 6. Психология и устойчивость»). Сравнение без учёта регистра, ё/е и
переносов строк внутри «…»."""
import os, re
from pathlib import Path
import yaml

KINDS = r"блок|блоки|модуль|модули|раздел|разделы|карточку|карточки"
SEP = r"(?:\s*,\s*|\s+и\s+)"
ONE = rf"(?:(?:{KINDS})\s+)?«[^«»]+»"
REF_RE = re.compile(rf"→\s*См\.\s+{ONE}(?:{SEP}{ONE})*")   # вся группа: «A», «B» и блок «C»
ITEM_RE = re.compile(rf"(?:({KINDS})\s+)?«([^«»]+)»")      # один заголовок в группе
MODULE_KINDS = ("блок", "модул", "раздел")
PLURAL = ("блоки", "модули", "разделы")  # «модули «A» и «B»» — маркер на всю группу

def flat(s):
    """Заголовок в одну строку: перенос внутри «…» (в т.ч. в цитате «> ») → пробел."""
    return " ".join(re.sub(r"\n[\s>]*", " ", s).split())

def norm(s):
    return flat(s).casefold().replace("ё", "е")

def module_title(path):
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "): return re.sub(r"^\d+\.\s*", "", line[2:]).strip()
    return None

def build_index(src):
    """{"card"|"module": {норм. заголовок: [пути от src]}}; список — чтобы видеть дубли."""
    idx = {"card": {}, "module": {}}
    for meta_p in sorted(src.rglob("*.meta.yml")):
        md = meta_p.with_suffix("").with_suffix(".md")
        title = (yaml.safe_load(meta_p.read_text(encoding="utf-8")) or {}).get("title")
        if title and md.exists():
            idx["card"].setdefault(norm(title), []).append(md.relative_to(src))
    for mod in sorted(src.rglob("_module.md")):
        t = module_title(mod)
        if not t: continue
        # «Жизнь с диабетом (по сценариям)» находится и как «Жизнь с диабетом»
        for alias in {norm(t), norm(re.sub(r"\s*\([^)]*\)$", "", t))}:
            idx["module"].setdefault(alias, []).append(mod.relative_to(src))
    return idx

def find_refs(text):
    """→ (номер строки, слово-маркер|None, заголовок, start, end); [start:end] — «…» с кавычками."""
    for m in REF_RE.finditer(text):
        kind = None
        for it in ITEM_RE.finditer(text, m.start(), m.end()):
            kind = it.group(1) or (kind if kind in PLURAL else None)
            yield text.count("\n", 0, it.start(2)) + 1, kind, it.group(2), it.start(2) - 1, it.end(2) + 1

def resolve(idx, kind, title):
    """→ (путь от src, None) или (None, причина). Сначала пространство по маркеру, потом другое."""
    order = ("module", "card") if kind and kind.startswith(MODULE_KINDS) else ("card", "module")
    for ns in order:
        hits = idx[ns].get(norm(title), [])
        if len(hits) == 1: return hits[0], None
        if hits: return None, "неоднозначна: " + ", ".join(map(str, hits))
    return None, "не найдена среди title карточек и заголовков модулей"

def broken_refs(src):
    """Для гейта: [(путь .md, строка, заголовок, причина)]."""
    idx = build_index(src); bad = []
    for md in sorted(src.rglob("*.md")):
        for line, kind, title, _, _ in find_refs(md.read_text(encoding="utf-8")):
            _, why = resolve(idx, kind, title)
            if why: bad.append((md, line, flat(title), why))
    return bad

def link_refs(text, here, idx, warn):
    """«Заголовок» после «→ См.» → «[Заголовок](относительный путь)».
    here — путь карточки от src; неразрешённая отсылка остаётся текстом + warn()."""
    out, last = [], 0
    for line, kind, title, s, e in find_refs(text):
        target, why = resolve(idx, kind, title)
        if why: warn(f"{here}:{line}: отсылка «{flat(title)}» {why} — оставлена текстом"); continue
        if target == here: continue  # отсылка на себя — ссылка не нужна
        rel = Path(os.path.relpath(target, here.parent)).as_posix()
        out += [text[last:s], f"«[{title}]({rel})»"]; last = e
    return "".join(out) + text[last:]
