import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

OWNER = "fjdev"
BOT_LOGINS = {"claude", "claude[bot]", "github-actions", "github-actions[bot]"}
ISSUE_LABELS = {"this-week", "idea"}
ISSUE_WAIT = timedelta(hours=48)
PR_WAIT = timedelta(hours=96)


@dataclass
class Item:
    number: int
    kind: Literal["issue", "pr"]
    labels: list[str]
    last_activity_by_owner: datetime | None
    last_activity_by_claude: datetime | None
    created_at: datetime
    reviewed: bool
    open: bool
    author: str = ""


def is_bot(login, flagged=False):
    return flagged or login.removeprefix("app/") in BOT_LOGINS


def _eligible(item, now):
    if not item.open or "nudged" in item.labels:
        return False
    if item.kind == "pr":
        return (
            not item.author.startswith("dependabot")
            and not item.reviewed
            and now - item.created_at >= PR_WAIT
        )
    if not ISSUE_LABELS & set(item.labels):
        return False
    bot_time = item.last_activity_by_claude
    if bot_time is None and is_bot(item.author):
        bot_time = item.created_at
    if bot_time is None:
        return False
    owner = item.last_activity_by_owner
    if owner is not None and owner >= bot_time:
        return False
    return now - bot_time >= ISSUE_WAIT


def select_nudges(items, now):
    return sorted(i.number for i in items if _eligible(i, now))


def _time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _latest(comments, wanted):
    times = [_time(c["createdAt"]) for c in comments if wanted(c["author"]["login"])]
    return max(times, default=None)


def _item(raw, kind):
    author = raw["author"]
    login = author["login"]
    comments = raw.get("comments", [])
    owner_time = _latest(comments, lambda who: who == OWNER)
    reviewed = bool(raw.get("reviews")) or owner_time is not None
    return Item(
        number=raw["number"],
        kind=kind,
        labels=[label["name"] for label in raw["labels"]],
        last_activity_by_owner=owner_time,
        last_activity_by_claude=_latest(comments, is_bot),
        created_at=_time(raw["createdAt"]),
        reviewed=reviewed if kind == "pr" else False,
        open=raw.get("state", "OPEN").upper() == "OPEN",
        author="dependabot[bot]" if login.removeprefix("app/") == "dependabot" else login,
    )


def parse(data):
    return [_item(r, "issue") for r in data["issues"]] + [_item(r, "pr") for r in data["prs"]]


def lines(items, now):
    chosen = set(select_nudges(items, now))
    return [f"{i.kind} {i.number}" for i in items if i.number in chosen]


def main():
    for line in lines(parse(json.load(sys.stdin)), datetime.now(timezone.utc)):
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
