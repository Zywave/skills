# AI Skills Library — Design

## Goal

Give insurance professionals (producers, account managers, producer managers) reusable
AI "skills" for Zywave workflows — e.g. researching a prospect, prepping a renewal, running
an outreach sequence — that work no matter which AI client they use: Claude, Claude Code
(IDE), ChatGPT, or Office365 Copilot.

These are business-workflow skills, not developer tooling. The audience for the skill
content itself is an insurance professional; the audience for this repo's structure and
generator is whoever authors and maintains skills (initially the Zywave team, with content
contributed by Producer Managers).

## Non-goals (this pass)

- Building real ChatGPT Actions or Office365 plugin backends. The Zywave MCP server is the
  only working integration today; ChatGPT/Office365 outputs are instructions-only, with a
  note about what connector/action the consumer still needs to wire up on their end.
- A CI drift check between `skills/` and `platforms/`. Explicitly deferred.
- Any UI, dashboard, or catalog site. This is files in a git repo.

## Authoring model

One canonical source per skill, directly usable by Claude and Claude Code with zero
transformation, plus generated (but checked-in) adaptations for platforms that can't
consume MCP tools the way Claude does.

**Why not per-platform authoring, or a fully separate abstract format:** Claude's native
skill format (YAML frontmatter + markdown body) is already close to platform-neutral prose,
and Claude/Claude Code are Zywave's primary target today since the MCP server is wired up
there. Making that format the canonical source means no translation layer for the platform
that matters most, while still allowing generation for the others.

## Repository layout

```
README.md
docs/
  authoring-guide.md              # how to write a new canonical skill (schema + style)
  platform-notes/
    claude.md                     # Claude / Claude Code consume skills/*/SKILL.md directly
    chatgpt.md                    # how to turn platforms/chatgpt output into a Custom GPT
    office365.md                  # how to turn platforms/office365 output into a declarative agent
skills/                           # canonical source — one folder per skill
  <skill-slug>/
    SKILL.md
platforms/                        # generated, committed to git (not gitignored)
  chatgpt/<skill-slug>/instructions.md
  office365/<skill-slug>/manifest.json
  office365/<skill-slug>/instructions.md
tools/
  generate-platforms.mjs          # Node script (no external dependencies), run manually
  package.json                    # just an npm script wrapper, no deps to install
```

`platforms/` output is committed so a consumer can grab the file for their platform straight
from GitHub without running anything. `tools/generate-platforms.mjs` is re-run by whoever
edits a skill, to keep `platforms/` in sync (manual — see Non-goals).

## Canonical skill format (`skills/<slug>/SKILL.md`)

Standard Claude skill frontmatter plus a few extra fields (Claude ignores unknown
frontmatter keys, so this stays a single source of truth). The generator reads `audience`
and `mcp_tools`; `category` is author-facing only (for browsing/grouping skills by eye) and
isn't currently consumed by the generator or by Claude:

```yaml
---
name: new-prospect-research-brief
description: Research a new company or household prospect and produce a research brief before outreach.
category: prospecting
audience: producer
mcp_tools:
  - discovery_company_search
  - discovery_household_search
  - discovery_company_contacts_get
  - discovery_household_contact_get
  - research_brief_generate
  - research_brief_get
---
```

Body: markdown instructions written the way an insurance producer would follow them —
when to use this skill, the steps, decision points, and what "done" looks like. References
Zywave MCP tools by name inline, the same way any Claude skill would.

## Generator (`tools/generate-platforms.mjs`)

Plain Node.js (ESM), no external npm dependencies — a small hand-written frontmatter parser
is enough for our controlled schema. For each `skills/*/SKILL.md`:

- **ChatGPT** (`platforms/chatgpt/<slug>/instructions.md`): the body rewritten as Custom GPT
  "Instructions" framing (second-person "You are a GPT that helps..."), plus a generated
  "Setup notes" section listing the `mcp_tools` and stating the consumer must connect an
  equivalent action/connector for each before this will work.
- **Office365** (`platforms/office365/<slug>/manifest.json` + `instructions.md`): a
  declarative-agent manifest skeleton (schema version, name, description, instructions file
  reference) plus the same adapted instructions body and setup notes.

Run via `npm run generate` (wraps `node tools/generate-platforms.mjs`) from `tools/`.

## Example skill: New Prospect Research Brief

`skills/new-prospect-research-brief/SKILL.md` — full worked example:

1. Producer names a company or household prospect.
2. Skill searches Market Discovery (`discovery_company_search` or `discovery_household_search`)
   to find the right MSID.
3. Pulls contacts (`discovery_company_contacts_get` / `discovery_household_contact_get`).
4. Kicks off `research_brief_generate`, polls `research_brief_get` until complete.
5. Presents the brief and suggests a next step (e.g. starting an outreach sequence).

This proves the end-to-end pattern; further skills (renewal content packages, outreach
sequences, etc.) follow the same shape and are expected to arrive from Producer Managers.

## Docs

- `docs/authoring-guide.md`: frontmatter schema, style guidance for writing steps an
  insurance professional (not a developer) can follow, and how to list `mcp_tools`.
- `docs/platform-notes/claude.md`: point Claude Desktop/claude.ai/Claude Code at `skills/`
  directly (e.g. copying a skill folder into `.claude/skills/` for Claude Code).
- `docs/platform-notes/chatgpt.md`: paste `platforms/chatgpt/<slug>/instructions.md` into a
  Custom GPT's Instructions field, then wire up the connector/action per the setup notes.
- `docs/platform-notes/office365.md`: use `platforms/office365/<slug>/manifest.json` +
  `instructions.md` as the starting point for a declarative agent in Copilot Studio.

## Open items for later passes

- Real ChatGPT Action / Office365 plugin wiring once Zywave exposes a stable REST/OpenAPI
  surface those platforms can call directly.
- CI check to keep `platforms/` in sync automatically.
- Additional skills from Producer Managers, following this same authoring model.
