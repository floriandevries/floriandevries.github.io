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
