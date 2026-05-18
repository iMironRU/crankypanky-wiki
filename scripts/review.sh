#!/usr/bin/env bash
# ИИ-предфильтр карточки (DeepSeek по умолчанию | OpenAI).
# Предфильтр, НЕ финальный допуск. Острое — только после человека.
#   ./scripts/review.sh <карточка.md> [модель]
set -euo pipefail
SD="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; RD="$(cd "$SD/.." && pwd)"
F="${1:-}"; MODEL="${2:-deepseek-chat}"
[[ -z "$F" || ! -f "$F" ]] && { echo "Использование: $0 <карточка.md> [модель]" >&2; exit 1; }
F="$F" SD="$SD" RD="$RD" MODEL="$MODEL" python3 - <<'PY'
import os,sys,json,re,urllib.request,urllib.error
from datetime import date
from pathlib import Path
F=Path(os.environ["F"]); RD=Path(os.environ["RD"]); MODEL=os.environ["MODEL"]
is_oa=MODEL.startswith(("gpt-","o1","o3","o4","chatgpt"))
env={}
ep=RD/".env"
if ep.exists():
    for ln in ep.read_text().splitlines():
        ln=ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k,v=ln.split("=",1); env[k.strip()]=v.strip()
if is_oa:
    key=env.get("OPENAI_API_KEY"); url="https://api.openai.com/v1/chat/completions"; lab="OpenAI"
else:
    key=env.get("DEEPSEEK_API_KEY"); url="https://api.deepseek.com/chat/completions"; lab="DeepSeek"
if not key: print("Нет API-ключа в .env",file=sys.stderr); sys.exit(1)
sysmsg=(RD/"scripts"/"prompts"/"reviewer.md").read_text(encoding="utf-8")
body=F.read_text(encoding="utf-8")
payload={"model":MODEL,"messages":[{"role":"system","content":sysmsg},
    {"role":"user","content":"Карточка на рецензию:\n\n"+body}],
    "temperature":0.3,"max_tokens":4096}
req=urllib.request.Request(url,data=json.dumps(payload).encode(),
    headers={"Content-Type":"application/json","Authorization":f"Bearer {key}"},method="POST")
print(f"Запрос в {lab} ({MODEL})...",flush=True)
try:
    r=json.loads(urllib.request.urlopen(req,timeout=120).read())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.read().decode('utf-8','replace')}",file=sys.stderr); sys.exit(1)
txt=r["choices"][0]["message"]["content"]; mu=r.get("model",MODEL)
rel=F.relative_to(RD/"content"); od=RD/"reviews"/rel.parts[0]; od.mkdir(parents=True,exist_ok=True)
out=od/f"{rel.stem}.{re.sub(r'[^a-z0-9-]','',mu.lower())[:20]}.{date.today().isoformat()}.md"
out.write_text(f"---\nfile: content/{rel}\nmodel: {mu}\ndate: {date.today().isoformat()}\n---\n\n"+txt,encoding="utf-8")
print("Рецензия:",out.relative_to(RD))
PY
