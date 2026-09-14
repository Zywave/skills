# Authoring a Skill

Skills in this repo are written for insurance professionals, not developers. Someone
reading the finished skill should recognize their own job in it — "research a prospect
before I call them", not "invoke the discovery API."

## Where a skill lives

Each skill is one folder under `skills/`, named with a lowercase, hyphenated slug that
matches its `name` frontmatter field:

```
skills/<slug>/SKILL.md
```

## Frontmatter schema

```yaml
---
name: my-skill-slug
description: One sentence a producer would recognize as "this is for me."
category: prospecting        # short label grouping related skills
audience: producer           # who uses this skill day-to-day
mcp_tools:                    # every Zywave MCP tool this skill calls
  - some_mcp_tool
  - another_mcp_tool
---
```

`name` and `description` are read by Claude's native skill mechanism — keep them accurate
and short. `category`, `audience`, and `mcp_tools` are read by the generator in `tools/` to
produce the ChatGPT and Office365 versions; they don't need to mean anything to Claude.

List every MCP tool the skill instructs the reader to call in `mcp_tools`, using the exact
tool name. The generator turns this into a checklist of what a ChatGPT or Office365
consumer needs to connect before the workflow will work for them.

## Writing the body

- Start with **"When to use this skill"** — the situation a producer is in when they'd
  reach for this.
- Write **steps as a numbered list**, in the order a person actually does them, including
  decision points ("if more than one match comes back, ask which one").
- Reference MCP tools by name inline, the same way you'd name a specific report or system a
  producer already uses.
- End with what "done" looks like, and a suggested next step when there is an obvious one.
- Avoid developer language ("call the endpoint", "the API returns") — say what happens in
  the producer's terms.

## After writing or editing a skill

Regenerate the platform outputs so `platforms/` stays in sync:

```bash
cd tools
npm run generate
```

Commit the changed files under `skills/` and `platforms/` together.
