# Zywave AI Skills

Reusable insurance-workflow skills for producers, account managers, and producer managers
— researching a prospect, sizing a territory, assembling a compliance notice packet,
running a prospecting campaign — built on Zywave's MCP tools.

Every skill is a single `skills/<slug>/SKILL.md` file, written in the open
[Agent Skills](https://agentskills.io) format (the same format Claude uses natively).
There's no per-platform conversion: any compliant AI client reads it directly — Claude,
Claude Code, GitHub Copilot/VS Code, Cursor, OpenAI Codex, Gemini CLI, Microsoft 365
Copilot Cowork, and more (see the full [client list](https://agentskills.io/clients)).

## Repository layout

```
skills/          every skill, one folder per slug — this is the whole deliverable
docs/            guide for writing a new skill, and how to install into each client
.claude-plugin/  marketplace + plugin manifests, so this repo installs as one Claude plugin
.agents/         marketplace manifest for ChatGPT/Codex's plugin import
plugin.json      generic plugin manifest read by the .agents/ marketplace above
```

## Skills

| Skill | What it does |
|---|---|
| [`book-of-business-audit`](skills/book-of-business-audit/) | Sweep the CRM book for data-quality issues (missing contacts, duplicates, stale records) into a workbook. Read-only. |
| [`cobra-notice-packet`](skills/cobra-notice-packet/) | Assemble the correct COBRA notice packet for a coverage-start, election, or termination event. |
| [`eb-annual-notice-packet`](skills/eb-annual-notice-packet/) | Assemble an employer's annual group health plan notice packet and distribution memo. |
| [`territory-market-map`](skills/territory-market-map/) | Size a sales territory or market from Zywave discovery data into a workbook and memo. |
| [`vertical-prospecting-campaign`](skills/vertical-prospecting-campaign/) | Run a full prospecting motion for one industry vertical, from ideal customer profile to a scheduled outreach sequence. |

## Adding or updating a skill

Read [`docs/authoring-guide.md`](docs/authoring-guide.md) and write or edit
`skills/<slug>/SKILL.md`. There's no build or generation step — the file you write is the
file every client reads.

## Using a skill

**Terminal, any client:** one command installs every skill here into any of 49 supported
clients — GitHub Copilot, Cursor, OpenAI Codex, Gemini CLI, Claude Code, and more:

```
gh skill install Zywave/skills --all
```

**Desktop or web app, no terminal:** see
[`docs/installing-skills.md`](docs/installing-skills.md) for the exact steps in the Claude
Desktop app, claude.ai, ChatGPT, Gemini Enterprise, and Microsoft 365 Copilot Cowork —
including the one-time marketplace setup (`/plugin marketplace add Zywave/skills` in
Claude Code, or a workspace admin importing this repo in ChatGPT) that makes every future
skill added here install automatically for already-connected users.

Every skill here assumes the Zywave MCP server is connected — without it, the tools a
skill calls out by name aren't available and it can't complete its steps.
