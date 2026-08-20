"""扫 data/proactive/*.json 生成 index.json，纯 proactive 界面开机读它。"""

import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # demo/
D = os.path.join(ROOT, "data", "proactive")

rows = []
for p in sorted(glob.glob(os.path.join(D, "*.json"))):
    name = os.path.basename(p)
    if name in ("index.json",) or name.endswith(".dropped.json"):
        continue
    d = json.load(open(p, encoding="utf-8"))
    if not d.get("tasks"):
        continue
    rows.append({
        "id": d["container_id"],
        "title": d["title"],
        "duration": d["video"]["duration"],
        "tasks": len(d["tasks"]),
    })

json.dump(rows, open(os.path.join(D, "index.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
for r in rows:
    print(f"  {r['id']:24} {r['tasks']:>3} 题  {r['duration']//60} 分钟")
print(f"写出 index.json（{len(rows)} 个 container）")
