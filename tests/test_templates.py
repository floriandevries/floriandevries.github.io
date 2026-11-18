from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / ".github" / "ISSUE_TEMPLATE"


def test_idea_template_applies_label():
    idea = yaml.safe_load((TEMPLATES / "idea.yml").read_text())
    assert idea["labels"] == ["idea"]

    body = {field["id"]: field for field in idea["body"]}
    assert body["what"]["type"] == "textarea"
    assert body["what"]["validations"]["required"] is True
    assert body["context"]["type"] == "textarea"
    assert not body["context"].get("validations", {}).get("required", False)

    config = yaml.safe_load((TEMPLATES / "config.yml").read_text())
    assert config["blank_issues_enabled"] is False
