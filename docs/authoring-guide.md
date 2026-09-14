# Authoring a Skill

Skills in this repo are written for insurance professionals, not developers. Someone
reading the finished skill should recognize their own job in it — "research a prospect
before I call them", not "invoke the discovery API."

This repo uses the open [Agent Skills](https://agentskills.io) format — the same format
Claude uses natively — as the *only* format. There's no per-platform conversion: any
compliant client (Claude, Claude Code, GitHub Copilot/VS Code, Cursor, OpenAI Codex,
Gemini CLI, Microsoft 365 Copilot Cowork, and others — see the full
[client list](https://agentskills.io/clients)) reads `skills/<slug>/SKILL.md` as-is.

## Where a skill lives

Each skill is one folder under `skills/`, named with a lowercase, hyphenated slug that
matches its `name` frontmatter field exactly:

```
skills/<slug>/SKILL.md
```

A skill folder may also contain, if useful:

```
skills/<slug>/
  SKILL.md
  scripts/      # executable code the skill runs (Python, Bash, JS, ...)
  references/   # detailed docs the reader loads only when needed
  assets/       # templates, lookup tables, other static resources
```

## Frontmatter

Only `name` and `description` are required:

```yaml
---
name: my-skill-slug
description: What this does, and specifically when to reach for it — this is the only
  thing loaded before the skill is activated, so front-load the situations and phrasing
  a producer would actually use.
---
```

- `name`: lowercase letters, numbers, and hyphens only; no leading/trailing/consecutive
  hyphens; must match the parent folder name exactly.
- `description`: up to 1024 characters. Describe both *what* the skill does and *when* to
  use it, with the specific words a producer or account manager would say — this is what a
  client matches against before deciding to load the rest of the file. Look at any existing
  skill in `skills/` for the level of specificity to aim for, including cross-references to
  a sibling skill when the boundary between them is easy to get wrong (e.g. "for sizing a
  whole territory use `territory-market-map`; for a single account use this one").

A few optional frontmatter fields exist in the spec (`license`, `compatibility`,
`allowed-tools`, and a `metadata` map for anything else) — most skills in this repo won't
need them. See the [full specification](https://agentskills.io/specification) if one seems
relevant.

## Writing the body

- Start with **"When to use this skill"** (or fold that into the description above, plus a
  short recap in the body) — the situation a producer is in when they'd reach for this.
- Write **steps as a numbered list**, in the order a person actually does them, including
  decision points ("if more than one match comes back, ask which one").
- Reference tools by name inline, the same way you'd name a specific report or system a
  producer already uses.
- End with what "done" looks like, and a suggested next step when there is an obvious one.
- Avoid developer language ("call the endpoint", "the API returns") — say what happens in
  the producer's terms.
- Keep `SKILL.md` itself short (the spec recommends under 500 lines). If a skill needs
  detailed lookup tables, long reference lists, or scripts, put those in `references/`,
  `assets/`, or `scripts/` and point to them from the body — the client only loads those
  files when the skill actually needs them.

## Validating a skill

Before committing a new or edited skill, check it against the spec using the
[skills-ref reference library](https://github.com/agentskills/agentskills/tree/main/skills-ref):

```bash
skills-ref validate skills/<slug>
```

See that repo for how to install `skills-ref` if it isn't already available.
