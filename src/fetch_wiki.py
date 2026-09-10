"""Fetch modern German (and some English) Wikipedia prose, politely and incrementally.

Gutenberg German is pre-reform orthography, which distorts letter frequencies (the 1996
reform moved real probability mass off 'ß'). Wikipedia gives contemporary orthography,
which is what actually gets typed today, so it is used for the held-out TEST set.

Saves after every batch: a long fetch that dies partway still leaves usable text.
"""

import json
import sys
import time
import urllib.error
import urllib.request

UA = {"User-Agent": "keyboard-layout-study/1.0 (personal research)"}


def api(lang):
    u = (
        f"https://{lang}.wikipedia.org/w/api.php?action=query&format=json"
        "&generator=random&grnnamespace=0&grnlimit=12"
        "&prop=extracts&explaintext=1&exlimit=12"
    )
    req = urllib.request.Request(u, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=60).read().decode("utf-8"))


def harvest(lang, target_chars, out_path):
    parts, total, backoff, since_save = [], 0, 1.0, 0
    fails = 0
    while total < target_chars and fails < 40:
        try:
            d = api(lang)
            backoff, fails = 1.0, 0
        except urllib.error.HTTPError as e:
            fails += 1
            if e.code == 429:
                backoff = min(backoff * 2, 30)
                time.sleep(backoff)
            else:
                time.sleep(3)
            continue
        except Exception:
            fails += 1
            time.sleep(3)
            continue

        for p in d.get("query", {}).get("pages", {}).values():
            t = p.get("extract", "")
            if len(t) > 600:
                parts.append(t)
                total += len(t)
                since_save += len(t)

        if since_save > 80_000:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write("\n\n".join(parts))
            since_save = 0
            print(f"  {lang}: {total:,} chars saved", flush=True)
        time.sleep(1.4)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts))
    print(f"  {lang}: FINAL {total:,} chars -> {out_path}", flush=True)
    return total


if __name__ == "__main__":
    de_target = int(sys.argv[1]) if len(sys.argv) > 1 else 900_000
    en_target = int(sys.argv[2]) if len(sys.argv) > 2 else 500_000
    print("German Wikipedia (modern orthography)...", flush=True)
    harvest("de", de_target, "corpus/_wiki_de.txt")
    print("English Wikipedia...", flush=True)
    harvest("en", en_target, "corpus/_wiki_en.txt")
    print("done")
