"""Snapshot of warframe.market sets: 90-day closed-trade history + top of book.

Sequential, at most 2.5 requests per second (documented limit is 3/s).
Usage: python3 -I collect.py <out_dir>
Writes <out_dir>/items.json, history.jsonl, book.jsonl and progress to stdout.
"""
import json
import sys
import time
import urllib.error
import urllib.request

OUT = sys.argv[1]
V1 = "https://api.warframe.market/v1"
V2 = "https://api.warframe.market/v2"
HEADERS = {
    "User-Agent": "wfm-trends-snapshot/1.0 (personal dashboard)",
    "Accept": "application/json",
    "Platform": "pc",
    "Language": "en",
    "Crossplay": "true",
}
MIN_INTERVAL = 0.4
_last = 0.0


def get(url):
    """GET with throttle and backoff. Returns parsed JSON, or None on 404."""
    global _last
    for attempt in range(6):
        wait = MIN_INTERVAL - (time.monotonic() - _last)
        if wait > 0:
            time.sleep(wait)
        _last = time.monotonic()
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if exc.code in (403, 429) or exc.code >= 500:
                delay = 2 ** (attempt + 1)
                print(f"HTTP {exc.code} on {url}; backing off {delay}s", flush=True)
                time.sleep(delay)
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            delay = 2 ** (attempt + 1)
            print(f"{exc!r} on {url}; backing off {delay}s", flush=True)
            time.sleep(delay)
    raise SystemExit(f"giving up on {url}")


items = get(f"{V2}/items")["data"]
sets = [i for i in items if "set" in i.get("tags", [])]
print(f"{len(items)} items, {len(sets)} sets", flush=True)
with open(f"{OUT}/items.json", "w") as fh:
    json.dump(sets, fh)

done = 0
missing = []
with open(f"{OUT}/history.jsonl", "w") as hist, open(f"{OUT}/book.jsonl", "w") as book:
    for item in sets:
        slug = item["slug"]
        stats = get(f"{V1}/items/{slug}/statistics")
        if stats is None:
            missing.append(slug)
            continue
        closed = stats["payload"]["statistics_closed"].get("90days", [])
        hist.write(json.dumps({"slug": slug, "days": closed}) + "\n")

        top = get(f"{V2}/orders/item/{slug}/top")
        data = (top or {}).get("data") or {}
        book.write(json.dumps({
            "slug": slug,
            "sell": [o.get("platinum") for o in data.get("sell", [])],
            "buy": [o.get("platinum") for o in data.get("buy", [])],
        }) + "\n")
        done += 1
        if done % 25 == 0:
            print(f"{done}/{len(sets)}", flush=True)

print(f"done {done}/{len(sets)}; missing: {missing}", flush=True)
