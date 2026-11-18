import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://floriandevries.github.io/"


def test_site_builds_with_correct_base(tmp_path):
    out = tmp_path / "public"
    result = subprocess.run(
        ["hugo", "--minify", "-d", str(out)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (out / "index.html").exists()
    assert (out / "index.xml").exists()

    html = (out / "index.html").read_text()
    urls = re.findall(r'(?:href|src)=["\']?(https?://[^"\'\s>]+)', html)
    own = [u for u in urls if "floriandevries.github.io" in u]
    assert own, "expected at least one absolute site URL in index.html"
    assert all(u.startswith(BASE) for u in own), own
