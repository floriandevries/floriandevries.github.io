import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from fjdev.content_check import split

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "lookback.json"
CONTENT_DIRS = ("content/posts", "content/snippets")


def previous_month(now):
    year, month = (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)
    return f"{year:04d}-{month:02d}"


def month_of(value):
    if isinstance(value, (date, datetime)):
        return value.strftime("%Y-%m")
    return str(value)[:7]


def summarize(posts, open_issues, month):
    in_month = [p for p in posts if month_of(p.get("date")) == month]
    return {
        "month": month,
        "published": len(in_month),
        "total": len(posts),
        "by_type": dict(Counter(p.get("kind") for p in in_month)),
        "waiting": len({i["number"] for i in open_issues}),
    }


def load_posts(root):
    posts = []
    for directory in CONTENT_DIRS:
        for path in sorted((root / directory).glob("*.md")):
            if path.name == "_index.md":
                continue
            front, _ = split(path.read_text(encoding="utf-8"))
            if front and front.get("date"):
                posts.append(front)
    return posts


def record(path, entry):
    entries = json.loads(path.read_text()) if path.exists() else []
    entries = [e for e in entries if e.get("month") != entry["month"]]
    entries.append(entry)
    path.write_text(json.dumps(entries, indent=2) + "\n")


def main(argv):
    parser = argparse.ArgumentParser(prog="lookback")
    parser.add_argument("--month")
    args = parser.parse_args(argv)
    month = args.month or previous_month(datetime.now(timezone.utc))
    summary = summarize(load_posts(ROOT), json.load(sys.stdin), month)
    record(DATA, summary)
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
