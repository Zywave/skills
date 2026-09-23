# Skills

Source of truth for every skill in the Zywave Skills Library. One folder per skill.

    skills/<slug>/
      SKILL.md          required — YAML frontmatter (name, description) + instructions
      references/       optional — docs the skill reads as needed
      scripts/          optional — deterministic helpers (Python, stdlib preferred)

Rules
- Folder name == frontmatter `name` == catalog `slug`.
- Description under 1024 characters, no unquoted colons (it's YAML).
- Zywave tool names as they appear in the MCP catalog (`content_search`, `account_search`, ...).
- Resolve library items by title; treat content IDs as hints, never as the retrieval key.
- Every write tool call sits behind an explicit user confirmation stated in the skill.
- No packaged `.skill` files in git. CI runs `scripts/package-skills.py`, which validates each
  folder and writes `static/skills/<slug>.skill` for the site to serve.

Adding a skill
1. Add the folder here.
2. Add a `skills:` entry in `data/catalog.yaml` with `package: /skills/<slug>.skill`.
3. Open an MR. The pipeline fails if the frontmatter is invalid.
