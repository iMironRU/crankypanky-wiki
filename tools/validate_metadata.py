#!/usr/bin/env python3
"""Гейт доверия. Падение = сборка падает.
Использование: python tools/validate_metadata.py content/"""
import sys, datetime
from pathlib import Path
try:
    import yaml
except ImportError:
    print("ERROR: pip install pyyaml"); sys.exit(1)
sys.path.insert(0, str(Path(__file__).parent))
from freshness import policy_max_cycle, state, next_review

REQUIRED = ["id","title","card_type","severity","disease_scope","audience","publish_state","signoff","freshness"]
CARD_TYPES=["knowledge","decision"]; SEVERITY=["acute","routine"]
PUB=["draft_verifying","published"]; SIGN=["pending","signed"]
FCLASS=["evergreen","slow","volatile"]


SD2_TRIPWIRE=["метформин","сд2","сахарный диабет 2","2 типа","sglt2","sglt-2",
              "преддиабет","инсулинорезистентн","пероральны"]
SD2_OK_CONTEXT=["не сд2","не про сд2","в отличие от сд2","это про сд2",
                "сд1 — это не сд2","сд1 ≠ сд2","относятся к сд2","относится к сд2",
                "не переносятся","не переносится","разные болезни","контраст"]

def lexical_sd2_check(meta_path):
    md=meta_path.with_suffix("").with_suffix(".md")
    if not md.exists(): return []
    low=md.read_text(encoding="utf-8").lower()
    if any(w in low for w in SD2_TRIPWIRE) and not any(c in low for c in SD2_OK_CONTEXT):
        return ["возможный занос СД2-логики без контрастного контекста (растяжитель — требует человеческой проверки)"]
    return []


VALID_ROLES={"self_adult","adolescent_transition","caregiver_of_child","caregiver_of_adult"}
TONE_CHILD=["ребёнок","ребенок","ребёнка","ребенка","ребёнку","ребенку","родител"]
TONE_OK=["и ребёнк","для ребёнка — школ","адресована всем","кто рядом",
         "и самому человеку","кем бы ни был читатель","права ребёнка"]

def audience_check(meta):
    a=meta.get("audience")
    if not isinstance(a,list) or not a:
        return ["audience обязан быть непустым списком ролей"]
    bad=[x for x in a if x not in VALID_ROLES]
    return [f"audience: недопустимые роли {bad}"] if bad else []

def tone_tripwire(meta, meta_path):
    a=set(meta.get("audience") or [])
    if not ({"self_adult","caregiver_of_adult","adolescent_transition"} & a):
        return []  # карточка только про ребёнка — детский тон законен
    md=meta_path.with_suffix("").with_suffix(".md")
    if not md.exists(): return []
    low=md.read_text(encoding="utf-8").lower()
    if any(w in low for w in TONE_CHILD) and not any(c in low for c in TONE_OK):
        return ["тон может быть захардкожен под ребёнка/родителя, а audience шире "
                "(растяжитель — требует человеческой проверки)"]
    return []

def check(meta, path):
    e=[]
    for f in REQUIRED:
        if f not in meta: e.append(f"нет поля {f}")
    if e: return e
    if meta["card_type"] not in CARD_TYPES: e.append("card_type невалиден")
    if meta["severity"] not in SEVERITY:     e.append("severity невалиден")
    if meta["publish_state"] not in PUB:     e.append("publish_state невалиден")
    if meta["signoff"] not in SIGN:          e.append("signoff невалиден")
    fr=meta["freshness"]; fc=fr.get("class")
    if fc not in FCLASS: e.append("freshness.class невалиден"); return e

    # класс ограничен типом карточки: decision обязан быть volatile
    if meta["card_type"]=="decision" and fc!="volatile":
        e.append("decision-карточка обязана иметь freshness.class: volatile")

    # цикл можно только УКОРОТИТЬ относительно максимума класса
    cyc=fr.get("review_cycle_months")
    pmax=policy_max_cycle(fc, meta["severity"])
    if cyc is None:
        if fc!="evergreen": e.append("review_cycle_months обязателен (не evergreen)")
    else:
        if cyc>pmax: e.append(f"review_cycle_months={cyc} превышает максимум {pmax} "
                              f"для class={fc}/severity={meta['severity']} (можно только укоротить)")

    # вычисляемые поля руками не пишут
    for forbidden in ("next_review","state"):
        if forbidden in fr: e.append(f"freshness.{forbidden} вычисляется, не пишется руками")

    # гейт: acute опубликован → обязан быть подписан человеком + иметь источники
    if meta["severity"]=="acute" and meta["publish_state"]=="published":
        if meta["signoff"]!="signed":
            e.append("acute + published требует signoff: signed (человеческая вычитка)")
        if not meta.get("clinical_refs"):
            e.append("acute + published требует непустой clinical_refs")
    if meta["severity"]=="acute" and meta["signoff"]=="signed" and not meta.get("clinical_refs"):
        e.append("acute + signoff: signed требует непустой clinical_refs")
    return e

def main():
    base=Path(sys.argv[1] if len(sys.argv)>1 else "content")
    files=sorted(base.rglob("*.meta.yml")); bad=0
    for mf in files:
        meta=yaml.safe_load(mf.read_text(encoding="utf-8")) or {}
        errs=check(meta, mf)+lexical_sd2_check(mf)+audience_check(meta)+tone_tripwire(meta, mf)
        if errs:
            bad+=1; print(f"FAIL {mf}")
            for x in errs: print(f"   - {x}")
    print(f"\nПроверено: {len(files)}, с ошибками: {bad}")
    sys.exit(1 if bad else 0)

if __name__=="__main__": main()
