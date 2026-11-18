import json
import shlex
from datetime import date, datetime

import yaml

from fjdev import lookback
from test_workflows import WORKFLOWS, assert_claude_steps_strict, claude_action_steps


def test_summarize_counts_by_type():
    posts = [
        {"kind": "how-to", "date": date(2026, 10, 3)},
        {"kind": "how-to", "date": datetime(2026, 10, 20, 8, 0)},
        {"kind": "snippet", "date": "2026-10-31"},
        {"kind": "opinion", "date": "2026-09-30"},
        {"kind": "exam-notes", "date": date(2026, 11, 1)},
    ]
    out = lookback.summarize(posts, [{"number": 1}, {"number": 2}], "2026-10")
    assert out == {
        "month": "2026-10",
        "published": 3,
        "by_type": {"how-to": 2, "snippet": 1},
        "waiting": 2,
    }


def test_previous_month_default():
    assert lookback.previous_month(datetime(2026, 11, 1)) == "2026-10"
    assert lookback.previous_month(datetime(2027, 1, 1)) == "2026-12"


def test_record_replaces_same_month(tmp_path):
    path = tmp_path / "lookback.json"
    path.write_text(json.dumps([{"month": "2026-09", "published": 1}]))
    lookback.record(path, {"month": "2026-10", "published": 2})
    lookback.record(path, {"month": "2026-10", "published": 5})
    assert json.loads(path.read_text()) == [
        {"month": "2026-09", "published": 1},
        {"month": "2026-10", "published": 5},
    ]


def test_lookback_commits_data_file():
    wf = yaml.safe_load((WORKFLOWS / "lookback.yml").read_text())
    assert wf[True]["schedule"] == [{"cron": "0 7 1 * *"}]
    jobs = wf["jobs"]
    assert assert_claude_steps_strict(jobs) == 1
    job = next(iter(jobs.values()))
    assert job["timeout-minutes"] == 15
    steps = job["steps"]
    commit = [
        i
        for i, s in enumerate(steps)
        if "git commit" in s.get("run", "") and "data/lookback.json" in s.get("run", "")
    ]
    claude = [i for i, s in enumerate(steps) if s.get("uses") == "anthropics/claude-code-action@v1"]
    assert commit and commit[0] < claude[0]
    assert steps[-1]["uses"] == "./.github/actions/report-failure"
    assert steps[-1]["if"] == "failure()"
    for _, step in claude_action_steps(jobs):
        args = shlex.split(step["with"]["claude_args"])
        tools = set(args[args.index("--allowedTools") + 1].split(","))
        assert tools == {"Bash(gh issue create:*)", "Bash(gh issue list:*)", "Read"}


def test_waiting_counts_each_item_once():
    items = [{"number": 1}, {"number": 1}, {"number": 2}]
    assert lookback.summarize([], items, "2026-10")["waiting"] == 2
