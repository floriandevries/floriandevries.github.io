import subprocess
import sys
from pathlib import Path

from fjdev.content_check import check_file

ROOT = Path(__file__).resolve().parent.parent


def make(tmp_path, body, **overrides):
    fields = {
        "title": "A title",
        "date": "2026-11-18",
        "kind": "how-to",
        "tags": "[terraform]",
        "summary": "Short summary.",
    }
    fields.update(overrides)
    head = "\n".join(f"{k}: {v}" for k, v in fields.items() if v is not None)
    p = tmp_path / "post.md"
    p.write_text(f"---\n{head}\n---\n\n{body}\n")
    return p


def words(n):
    return " ".join(["word"] * n)


def test_valid_post_passes(tmp_path):
    assert check_file(make(tmp_path, words(400)), []) == []


def test_missing_field_fails(tmp_path):
    errors = check_file(make(tmp_path, words(400), summary=None), [])
    assert len(errors) == 1 and "summary" in errors[0]


def test_post_word_count_bounds(tmp_path):
    for n in (250, 650):
        errors = check_file(make(tmp_path, words(n)), [])
        assert len(errors) == 1 and "300-600" in errors[0]


def test_code_fences_not_counted(tmp_path):
    body = words(400) + "\n\n```\n" + words(500) + "\n```\n"
    assert check_file(make(tmp_path, body), []) == []


def test_snippet_needs_code_block(tmp_path):
    p = make(tmp_path, "Just prose.", kind="snippet")
    assert any("code block" in e for e in check_file(p, []))
    p = make(tmp_path, "Prose.\n\n```hcl\nmoved {}\n```", kind="snippet")
    assert check_file(p, []) == []


def test_denylisted_term_fails(tmp_path):
    p = make(tmp_path, words(400) + " Contoso")
    errors = check_file(p, ["contoso"])
    assert len(errors) == 1 and "denylist" in errors[0]
    assert "contoso" not in errors[0].lower().replace("denylist", "")


def test_denylist_whole_word_and_title(tmp_path):
    assert check_file(make(tmp_path, words(400) + " Contosoland"), ["contoso"]) == []
    p = make(tmp_path, words(400), title="About CONTOSO")
    assert any("denylist" in e for e in check_file(p, [" contoso ", ""]))


def test_unknown_type_fails(tmp_path):
    errors = check_file(make(tmp_path, words(400), kind="news"), [])
    assert any("type" in e and "kind" in e for e in errors)
    assert check_file(make(tmp_path, words(400), kind=None), []) == ["missing field: kind"]


def test_bad_date_summary_tags(tmp_path):
    assert check_file(make(tmp_path, words(400), date="2026-11-18T07:00:00Z"), []) == []
    assert any("date" in e for e in check_file(make(tmp_path, words(400), date="soon"), []))
    assert any("summary" in e for e in check_file(make(tmp_path, words(400), summary="x" * 161), []))
    assert any("tags" in e for e in check_file(make(tmp_path, words(400), tags="[]"), []))


def test_cli(tmp_path):
    posts = tmp_path / "content" / "posts"
    posts.mkdir(parents=True)
    (tmp_path / "content" / "about.md").write_text("no front matter")
    (posts / "_index.md").write_text("no front matter")
    (posts / "bad.md").write_text(make(tmp_path, words(10)).read_text())
    env = {"PYTHONPATH": str(ROOT / "scripts"), "FJDEV_DENYLIST": ""}
    r = subprocess.run([sys.executable, "-m", "fjdev.content_check", str(tmp_path / "content")],
                       capture_output=True, text=True, env=env)
    assert r.returncode == 1
    assert "bad.md: " in r.stdout and "300-600" in r.stdout
    assert "::warning::FJDEV_DENYLIST is empty; denylist check skipped" in r.stdout
    assert "about.md" not in r.stdout and "_index" not in r.stdout


def test_malformed_yaml_reports_without_leaking(tmp_path):
    p = tmp_path / "bad.md"
    p.write_text('---\ntitle: "Contoso unclosed\nkind: how-to\n---\n\nbody\n')
    errors = check_file(p, ["contoso"])
    assert errors == ["missing or invalid front matter"]
    p.write_bytes(b"---\n\xff\xfe\n---\n")
    assert check_file(p, []) == ["missing or invalid front matter"]


def test_denylist_multiword_whitespace(tmp_path):
    for sep in ("  ", "\t", "\n"):
        p = make(tmp_path, words(400) + f" A.B{sep}Corp")
        assert any("denylist" in e for e in check_file(p, ["A.B Corp"]))
