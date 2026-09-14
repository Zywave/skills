# Using a skill in ChatGPT

ChatGPT doesn't read `skills/` directly — use the generated file at
`platforms/chatgpt/<slug>/instructions.md` instead.

## Steps

1. In ChatGPT, create or edit a Custom GPT.
2. Open `platforms/chatgpt/<slug>/instructions.md` and copy everything under
   "## Instructions" (skip the "Setup notes" section) into the GPT's **Instructions** field.
3. Read the "## Setup notes" section in that same file — it lists the Zywave capabilities
   this skill needs. Connect an Action or MCP connector in the GPT builder that provides
   each one before publishing the GPT.
4. Test the GPT with a real scenario from the skill's "When to use this skill" section
   before sharing it.

## Keeping it in sync

`instructions.md` is generated from `skills/<slug>/SKILL.md` — don't hand-edit it. If the
skill changes, re-run the generator (see [`../authoring-guide.md`](../authoring-guide.md))
and re-paste the updated instructions into the GPT.
