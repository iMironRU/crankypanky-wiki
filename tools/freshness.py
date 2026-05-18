"""Единый расчёт свежести. next_review / state / banner — ТОЛЬКО здесь.
Руками в .meta.yml эти значения не пишутся."""
from datetime import date
from dateutil.relativedelta import relativedelta  # python-dateutil

CLASS_MAX = {"evergreen": 36, "slow": 12, "volatile": 3}

def policy_max_cycle(fclass, severity):
    m = CLASS_MAX[fclass]
    if severity == "acute":
        m = min(m, 3)          # острое форсирует короткий цикл
    return m

def next_review(last_reviewed, cycle_months):
    return last_reviewed + relativedelta(months=cycle_months)

def state(last_reviewed, cycle_months, today=None):
    today = today or date.today()
    nr = next_review(last_reviewed, cycle_months)
    warn = nr - relativedelta(days=max(30, int(cycle_months*30*0.2)))
    if today >= nr:   return "overdue"
    if today >= warn: return "due_soon"
    return "fresh"

def banner_severity(card_severity, st, months_overdue):
    """Громкость публичного баннера — функция от данных, не одна строка."""
    if st == "fresh":               return None
    if card_severity == "acute":    return "loud"      # острое + не fresh → громкий
    if st == "overdue" and months_overdue >= 6: return "loud"
    if st == "overdue":             return "normal"
    return "soft"                                       # due_soon, routine
