import json
from datetime import datetime, timedelta, timezone

from fjdev import nudge
from fjdev.nudge import Item, select_nudges

NOW = datetime(2026, 11, 18, 7, 0, tzinfo=timezone.utc)


def ago(hours):
    return NOW - timedelta(hours=hours)


def issue(hours, **kw):
    base = dict(number=1, kind="issue", labels=["this-week"], last_activity_by_owner=None,
                last_activity_by_claude=ago(hours), created_at=ago(hours + 1), reviewed=False,
                open=True, author="fjdev")
    return Item(**{**base, **kw})


def pr(hours, **kw):
    base = dict(number=2, kind="pr", labels=[], last_activity_by_owner=None,
                last_activity_by_claude=None, created_at=ago(hours), reviewed=False,
                open=True, author="claude[bot]")
    return Item(**{**base, **kw})


def test_issue_waiting_two_days_is_nudged():
    assert select_nudges([issue(49)], NOW) == [1]


def test_issue_under_two_days_not_nudged():
    assert select_nudges([issue(47)], NOW) == []


def test_pr_unreviewed_four_days_is_nudged():
    assert select_nudges([pr(97)], NOW) == [2]
    assert select_nudges([pr(95)], NOW) == []


def test_item_never_nudged_twice():
    assert select_nudges([issue(99, labels=["this-week", "nudged"]), pr(99, labels=["nudged"])], NOW) == []


def test_closed_items_ignored():
    assert select_nudges([issue(99, open=False), pr(99, open=False)], NOW) == []


def test_dependabot_prs_not_nudged():
    assert select_nudges([pr(240, author="dependabot[bot]")], NOW) == []


def test_owner_reply_after_claude_stops_nudge():
    assert select_nudges([issue(60, last_activity_by_owner=ago(10))], NOW) == []


def test_bot_authored_issue_without_comments_is_nudged():
    item = issue(0, last_activity_by_claude=None, created_at=ago(49), author="github-actions[bot]")
    assert select_nudges([item], NOW) == [1]


def test_unlabelled_issue_not_nudged():
    assert select_nudges([issue(99, labels=["bug"])], NOW) == []


def test_cli_parses_gh_json():
    data = {
        "issues": [{
            "number": 5, "state": "OPEN", "createdAt": "2026-11-10T06:00:00Z",
            "labels": [{"name": "this-week"}],
            "author": {"login": "app/github-actions", "is_bot": True},
            "comments": [{"author": {"login": "claude"}, "createdAt": "2026-11-14T06:00:00Z"}],
        }],
        "prs": [{
            "number": 6, "state": "OPEN", "createdAt": "2026-11-10T06:00:00Z",
            "labels": [], "author": {"login": "claude", "is_bot": True},
            "reviews": [], "comments": [{"author": {"login": "fjdev"}, "createdAt": "2026-11-11T06:00:00Z"}],
        }, {
            "number": 7, "state": "OPEN", "createdAt": "2026-11-10T06:00:00Z",
            "labels": [], "author": {"login": "claude", "is_bot": True},
            "reviews": [], "comments": [],
        }],
    }
    items = nudge.parse(data)
    assert [(i.number, i.kind, i.reviewed) for i in items] == [(5, "issue", False), (6, "pr", True), (7, "pr", False)]
    assert nudge.lines(items, NOW) == ["issue 5", "pr 7"]
    json.dumps(data)


def test_cli_honours_is_bot_flag():
    data = {
        "issues": [{
            "number": 8, "state": "OPEN", "createdAt": "2026-11-10T06:00:00Z",
            "labels": [{"name": "idea"}],
            "author": {"login": "some-app", "is_bot": True},
            "comments": [],
        }],
        "prs": [],
    }
    assert nudge.lines(nudge.parse(data), NOW) == ["issue 8"]
