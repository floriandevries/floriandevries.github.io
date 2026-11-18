# Rules for Claude in this repo

- Read `STYLE.md` before writing anything.
- Start new content from the archetypes: `hugo new posts/<slug>.md` or `hugo new snippets/<slug>.md`.
- Use only facts, opinions and examples Florian wrote in the issue thread. Never invent experiences, numbers or quotes.
- Run `PYTHONPATH=scripts python -m fjdev.content_check content/` and fix every error before opening a PR.
- Work only on a `claude/<slug>` branch and open a PR that links the issue with `Refs #N`.
- Claude must never merge, never push to `main`, never publish. In short: never merge.
- Never read or reference other repositories or client material.
- Keep replies in issues short. Florian reads them on his phone.
