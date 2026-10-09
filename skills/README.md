# Skills

Source of truth for every skill in the Zywave Skills Library. One folder per skill.

    skills/<slug>/
      SKILL.md          required — YAML frontmatter (name, description) + instructions
      references/       optional — docs the skill reads as needed
      scripts/          optional — deterministic helpers (Python, stdlib preferred)
      assets/           optional — templates, lookup tables, other static resources

Rules
- Folder name == frontmatter `name`.
- Description under 1024 characters, no unquoted colons (it's YAML).
- Zywave tool names as they appear in the MCP catalog (`content_search`, `account_search`, ...).
- Resolve library items by title; treat content IDs as hints, never as the retrieval key.
- Every write tool call sits behind an explicit user confirmation stated in the skill.
- No build or packaging step. The folder you commit is what every client installs.

Adding a skill
1. Read `docs/authoring-guide.md` and add the folder here.
2. Add a row to the skills table in the root `README.md`.
3. Open a PR.
