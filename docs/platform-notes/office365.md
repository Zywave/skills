# Using a skill in Office365 Copilot

Office365 Copilot doesn't read `skills/` directly — use the generated files at
`platforms/office365/<slug>/` instead.

## Steps

1. In Copilot Studio (or the Microsoft 365 Agents Toolkit), start a new declarative agent.
2. Use `platforms/office365/<slug>/manifest.json` as the starting point for the agent's
   manifest. You may need to adjust the `$schema`/`version` fields to match the schema
   version your tooling currently expects.
3. Use `platforms/office365/<slug>/instructions.md` as the agent's instructions — copy
   everything under "## Instructions" (skip the "Setup notes" section).
4. Read the "## Setup notes" section — it lists the Zywave capabilities this skill needs.
   Connect a plugin or MCP connector that provides each one before publishing the agent.
5. Test the agent with a real scenario from the skill's "When to use this skill" section
   before sharing it.

## Keeping it in sync

Both files are generated from `skills/<slug>/SKILL.md` — don't hand-edit them. If the skill
changes, re-run the generator (see [`../authoring-guide.md`](../authoring-guide.md)) and
re-apply the updated manifest/instructions in Copilot Studio.
