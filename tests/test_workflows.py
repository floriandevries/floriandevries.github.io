import shlex
from pathlib import Path

import yaml

WORKFLOWS = Path(__file__).resolve().parent.parent / ".github" / "workflows"
ACTION = "anthropics/claude-code-action@v1"


def claude_action_steps(jobs):
    for name, job in jobs.items():
        for step in job["steps"]:
            if step.get("uses") == ACTION:
                yield name, step


def assert_claude_steps_strict(jobs):
    count = 0
    for name, step in claude_action_steps(jobs):
        count += 1
        args = step["with"]["claude_args"]
        assert "--max-turns 10" in args, name
        assert "--permission-mode acceptEdits" in args, name
    assert count
    return count


def test_claude_workflow_restricted_to_owner():
    text = (WORKFLOWS / "claude.yml").read_text()
    assert "ANTHROPIC_API_KEY" not in text
    assert "anthropic_api_key" not in text
    jobs = yaml.safe_load(text)["jobs"]
    assert jobs
    action_steps = 0
    for name, job in jobs.items():
        assert "github.actor == 'fjdev'" in job["if"], name
        assert job["timeout-minutes"] == 15, name
        assert job["concurrency"]["group"].startswith(f"claude-{name}-"), name
        for step in job["steps"]:
            if step.get("uses") != ACTION:
                continue
            action_steps += 1
            with_ = step["with"]
            assert (
                with_["claude_code_oauth_token"]
                == "${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}"
            ), name
    assert action_steps == len(jobs)
    assert assert_claude_steps_strict(jobs) == len(jobs)


def load(name):
    return yaml.safe_load((WORKFLOWS / name).read_text())


def test_scout_tools_limited():
    wf = load("scout.yml")
    assert wf["permissions"]["contents"] == "read"
    tools = set()
    for _, step in claude_action_steps(wf["jobs"]):
        args = shlex.split(step["with"]["claude_args"])
        tools |= set(args[args.index("--allowedTools") + 1].split(","))
    assert tools == {
        "Bash(gh issue create:*)",
        "Bash(gh issue list:*)",
        "WebFetch",
        "WebSearch",
    }


def test_scheduled_workflows_report_failure():
    for name in ("weekly.yml", "scout.yml"):
        jobs = load(name)["jobs"]
        assert assert_claude_steps_strict(jobs) == 1
        for job in jobs.values():
            last = job["steps"][-1]
            assert last["uses"] == "./.github/actions/report-failure", name
            assert last["if"] == "failure()", name


def tool_list(step, flag):
    args = shlex.split(step["with"]["claude_args"])
    return args[args.index(flag) + 1].split(",") if flag in args else []


def test_no_bare_edit_or_write_tools():
    for path in WORKFLOWS.glob("*.yml"):
        for name, step in claude_action_steps(yaml.safe_load(path.read_text())["jobs"]):
            tools = tool_list(step, "--allowedTools")
            assert not {"Edit", "Write", "MultiEdit"} & set(tools), (path.name, name)


def test_respond_job_limits_input_and_edits():
    respond = load("claude.yml")["jobs"]["respond"]
    (_, step), = claude_action_steps({"respond": respond})
    assert step["with"]["include_comments_by_actor"] == "fjdev,claude[bot]"
    denied = set(tool_list(step, "--disallowedTools"))
    assert {"Edit(scripts/**)", "Edit(.github/**)"} <= denied
