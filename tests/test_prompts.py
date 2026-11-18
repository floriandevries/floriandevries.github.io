from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_prompt_files_exist_and_reference_style():
    for name in ("followup", "draft", "linkedin"):
        assert (ROOT / "prompts" / f"{name}.md").is_file()
    for name in ("draft", "linkedin"):
        assert "STYLE.md" in (ROOT / "prompts" / f"{name}.md").read_text()
    assert "never merge" in (ROOT / "CLAUDE.md").read_text()
