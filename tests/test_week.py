from datetime import datetime

from fjdev.week import find_open_week_issue, week_title


def test_week_title_iso():
    assert week_title(datetime(2026, 11, 16)) == "This week: 2026-W47"
    assert week_title(datetime(2027, 1, 1)) == "This week: 2026-W53"


def test_existing_week_issue_is_reused():
    t = "This week: 2026-W47"
    issues = [
        {"number": 3, "title": t, "state": "CLOSED"},
        {"number": 5, "title": "other", "state": "OPEN"},
        {"number": 9, "title": t, "state": "OPEN"},
    ]
    assert find_open_week_issue(issues, t) == 9
    assert find_open_week_issue(issues[:2], t) is None
