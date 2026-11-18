import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

POST_TYPES = {"how-to", "release-take", "exam-notes", "opinion"}
TYPES = POST_TYPES | {"snippet"}
FIELDS = ("title", "date", "type", "tags", "summary")
FENCE = re.compile(r"^\s*(```|~~~)")


def split(text):
    m = re.match(r"---\r?\n(.*?)\r?\n---\r?\n?(.*)", text, re.S)
    if not m:
        return None, text
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None, text
    return (data if isinstance(data, dict) else None), m.group(2)


def prose_and_fences(body):
    prose, fences, inside = [], 0, False
    for line in body.splitlines():
        if FENCE.match(line):
            if not inside:
                fences += 1
            inside = not inside
        elif not inside:
            prose.append(line)
    return "\n".join(prose), fences


def check_file(path, denylist):
    try:
        text = Path(path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["missing or invalid front matter"]
    meta, body = split(text)
    if meta is None:
        return ["missing or invalid front matter"]
    errors = [f"missing field: {f}" for f in FIELDS if meta.get(f) in (None, "", [])]

    if "date" in meta and meta["date"] not in (None, "") and not isinstance(meta["date"], (date, datetime)):
        errors.append("date is not a valid date")
    summary = meta.get("summary")
    if summary not in (None, "") and (not isinstance(summary, str) or len(summary) > 160):
        errors.append("summary must be a string of at most 160 characters")
    tags = meta.get("tags")
    if tags not in (None, []) and not (isinstance(tags, list) and all(isinstance(t, str) for t in tags)):
        errors.append("tags must be a list of strings")

    kind = meta.get("type")
    prose, fences = prose_and_fences(body)
    if kind in (None, ""):
        pass
    elif kind not in TYPES:
        errors.append(f"unknown type; expected one of {', '.join(sorted(TYPES))}")
    elif kind == "snippet":
        if not fences:
            errors.append("snippet needs a fenced code block")
    else:
        count = len(prose.split())
        if not 300 <= count <= 600:
            errors.append(f"post body must be 300-600 words, found {count}")

    haystack = " ".join(
        [str(meta.get("title") or ""), str(meta.get("summary") or ""), " ".join(map(str, tags or [])), body]
    )
    haystack = re.sub(r"\s+", " ", haystack)
    for term in denylist:
        term = re.sub(r"\s+", " ", term)
        if re.search(rf"(?<!\w){re.escape(term)}(?!\w)", haystack, re.I):
            errors.append("denylist term found; remove or generalise it")
            break
    return errors


def main(argv):
    root = Path(argv[1] if len(argv) > 1 else "content")
    denylist = [t.strip() for t in os.environ.get("FJDEV_DENYLIST", "").split(",") if t.strip()]
    if not denylist:
        print("::warning::FJDEV_DENYLIST is empty; denylist check skipped")
    failed = False
    for path in sorted(root.rglob("*.md")):
        parts = path.relative_to(root).parts if path.is_relative_to(root) else path.parts
        if path.name == "_index.md" or parts[0] not in ("posts", "snippets"):
            continue
        for err in check_file(path, denylist):
            print(f"{path}: {err}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
