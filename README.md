# Zywave AI Skills

Repository for AI Zywave LLM skills that are primarily enabled by the Zywave MCP server.

These skills give insurance professionals (producers, account managers, producer managers)
reusable workflows — researching a prospect, prepping a renewal, running an outreach
sequence — that work across the AI clients Zywave supports:

- **Claude** (claude.ai, Claude Desktop) and **Claude Code** — skills are consumed directly
  from `skills/`, no conversion needed.
- **ChatGPT** — via a Custom GPT, using the adapted instructions generated into
  `platforms/chatgpt/`.
- **Office365 Copilot** — via a declarative agent, using the manifest and instructions
  generated into `platforms/office365/`.

## Repository layout

```
skills/     canonical skill source — author here
platforms/  generated ChatGPT/Office365 outputs (committed, not hand-edited)
docs/       authoring guide + per-platform setup notes
tools/      generator script that produces platforms/ from skills/
```

## Adding or updating a skill

1. Read [`docs/authoring-guide.md`](docs/authoring-guide.md) and write or edit
   `skills/<slug>/SKILL.md`.
2. Regenerate the platform outputs:
   ```bash
   cd tools
   npm run generate
   ```
3. Commit `skills/` and `platforms/` together.

## Using a skill

- **Claude / Claude Code:** see [`docs/platform-notes/claude.md`](docs/platform-notes/claude.md).
- **ChatGPT:** see [`docs/platform-notes/chatgpt.md`](docs/platform-notes/chatgpt.md).
- **Office365 Copilot:** see [`docs/platform-notes/office365.md`](docs/platform-notes/office365.md).
