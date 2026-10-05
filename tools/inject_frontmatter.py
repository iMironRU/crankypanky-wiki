#!/usr/bin/env python3
"""Собирает build/ : .md + инжект фронтматтера из .meta.yml,
отсылки «→ См. «…»» → ссылки (tools/crossrefs.py),
плюс генерит индекс «Можно ли…?» и дашборд свежести."""
import sys, shutil, datetime, re
from pathlib import Path
import yaml
sys.path.insert(0, str(Path(__file__).parent))
from freshness import next_review, state, banner_severity, policy_max_cycle
from crossrefs import build_index, link_refs

SRC=Path("content"); OUT=Path("build")
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()

DOI_RE=re.compile(r"doi:\s*(10\.\S+?)[.,;]?(?:\s|$)")

def sources(meta):
    """Источники для показа на странице: clinical_refs (строки; DOI → ссылка)
    и external_references (title/url/note)."""
    out=[]
    for r in meta.get("clinical_refs") or []:
        m=DOI_RE.search(str(r)+" ")
        out.append({"text":str(r),"url":f"https://doi.org/{m.group(1)}" if m else None})
    for r in meta.get("external_references") or []:
        if isinstance(r,dict) and r.get("title"):
            out.append({"text":r["title"],"url":r.get("url") or None,"note":r.get("note") or None})
    return out

def parse_date(v):
    if isinstance(v, datetime.date): return v
    return datetime.date.fromisoformat(str(v))

rows=[]; mozhno=[]; idx=build_index(SRC); warns=[]
for md in sorted(SRC.rglob("*.md")):
    rel=md.relative_to(SRC)
    meta_p=md.with_suffix(".meta.yml")
    text=link_refs(md.read_text(encoding="utf-8"),rel,idx,warns.append)
    fm={}
    if meta_p.exists():
        meta=yaml.safe_load(meta_p.read_text(encoding="utf-8")) or {}
        fr=meta.get("freshness",{})
        lr=parse_date(fr.get("last_reviewed")) if fr.get("last_reviewed") else None
        cyc=fr.get("review_cycle_months") or policy_max_cycle(fr.get("class","slow"),meta.get("severity","routine"))
        st=banner=None; nr=None
        if lr:
            nr=next_review(lr,cyc); st=state(lr,cyc)
            mo=max(0,(datetime.date.today()-nr).days//30)
            banner=banner_severity(meta.get("severity","routine"),st,mo)
        fm={"title":meta.get("title"),"card_type":meta.get("card_type"),
            "severity":meta.get("severity"),"publish_state":meta.get("publish_state"),
            "freshness_state":st,"last_reviewed":str(lr) if lr else None,
            "next_review":str(nr) if nr else None,
            "banner":banner,"sources":sources(meta)}
        rows.append((str(rel),meta.get("severity"),st,str(nr) if nr else "—",
                     meta.get("publish_state")))
        if "mozhno-li" in (meta.get("tags") or []):
            mozhno.append((meta.get("title"),str(rel)))
    dst=OUT/rel; dst.parent.mkdir(parents=True,exist_ok=True)
    head="---\n"+yaml.safe_dump(fm,allow_unicode=True,sort_keys=False)+"---\n\n" if fm else ""
    dst.write_text(head+text,encoding="utf-8")

# индекс «Можно ли…?» — генерируется, не ведётся руками
idx=["# Можно ли…? — быстрые ответы\n",
     "> Индекс собран автоматически из карточек с тегом `mozhno-li`.\n"]
for t,r in sorted(mozhno): idx.append(f"- [{t}]({r})")
(OUT/"mozhno-li.md").write_text("\n".join(idx)+"\n",encoding="utf-8")

# дашборд свежести — то, ради чего был разговор про устаревание
d=["# Дашборд свежести\n","| Карточка | severity | состояние | next_review | публикация |",
   "|---|---|---|---|---|"]
order={"overdue":0,"due_soon":1,"fresh":2,None:3}
for r,sev,st,nr,pub in sorted(rows,key=lambda x:order.get(x[2],3)):
    d.append(f"| {r} | {sev} | **{st}** | {nr} | {pub} |")
(OUT/"freshness-dashboard.md").write_text("\n".join(d)+"\n",encoding="utf-8")

(OUT/"index.md").write_text(
    "# CrankyPanky — база знаний\n\n"
    "Информационно-образовательный ресурс для семей с СД1.\n\n"
    "- [Можно ли…?](mozhno-li.md)\n- [Дашборд свежести](freshness-dashboard.md)\n\n"
    "> Обучающая информация, не персональные медицинские рекомендации.\n",
    encoding="utf-8")
for w in warns: print(f"WARN {w}",file=sys.stderr)
print("build/ собран"+(f", неразрешённых отсылок: {len(warns)}" if warns else ""))
