"""Turn the raw snapshot into the two CSV files the dashboard attaches.

Usage: python3 -I build.py <raw_dir> <out_dir>
"""
import collections
import csv
import json
import statistics
import sys

RAW, OUT = sys.argv[1], sys.argv[2]
ORDER = [
    "Warframes",
    "Armas primárias",
    "Armas secundárias",
    "Corpo a corpo",
    "Archwing e Necramech",
    "Companheiros e outros",
]


def category(tags):
    tags = set(tags)
    if tags & {"archwing", "necramech", "mech"}:
        return "Archwing e Necramech"
    if "warframe" in tags:
        return "Warframes"
    if "primary" in tags:
        return "Armas primárias"
    if "secondary" in tags:
        return "Armas secundárias"
    if "melee" in tags:
        return "Corpo a corpo"
    return "Companheiros e outros"


def jsonl(path):
    with open(path) as fh:
        return [json.loads(line) for line in fh]


sets = json.load(open(f"{RAW}/items.json"))
book = {row["slug"]: row for row in jsonl(f"{RAW}/book.jsonl")}
history = {row["slug"]: row["days"] for row in jsonl(f"{RAW}/history.jsonl")}

rows = []
for item in sets:
    slug = item["slug"]
    top = book.get(slug, {})
    rows.append({
        "slug": slug,
        "nome": item["i18n"]["en"]["name"],
        "categoria": category(item["tags"]),
        "prime": "sim" if "prime" in item["tags"] else "não",
        "ducats": item.get("ducats", ""),
        "melhor_venda": min(top.get("sell") or [""], default=""),
        "melhor_compra": max(top.get("buy") or [""], default=""),
    })
rows.sort(key=lambda r: (ORDER.index(r["categoria"]), r["nome"]))

with open(f"{OUT}/itens.csv", "w", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

count = 0
flagged = []
with open(f"{OUT}/historico.csv", "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["dia", "slug", "vendas", "mediana", "media", "minimo", "maximo", "suspeito"])
    for row in rows:
        days = history.get(row["slug"], [])
        if not days:
            continue
        typical_price = statistics.median(d["median"] for d in days)
        typical_sales = statistics.median(d["volume"] for d in days)
        for day in days:
            odd = day["median"] >= 10 * typical_price or day["volume"] >= 20 * typical_sales
            if odd:
                flagged.append((row["slug"], day["datetime"][:10], day["volume"], day["median"]))
            writer.writerow([
                day["datetime"][:10], row["slug"], day["volume"], day["median"],
                day["wa_price"], day["min_price"], day["max_price"], "sim" if odd else "não",
            ])
            count += 1

print(f"itens: {len(rows)}; historico: {count} rows; flagged: {flagged}")
print(collections.Counter(r["categoria"] for r in rows))
print("without any history:", [r["slug"] for r in rows if not history.get(r["slug"])])
print("without best sell:", sum(r["melhor_venda"] == "" for r in rows),
      "without best buy:", sum(r["melhor_compra"] == "" for r in rows))
