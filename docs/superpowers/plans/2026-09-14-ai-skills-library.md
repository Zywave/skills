# AI Skills Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the AI Skills library scaffolding — canonical skill source format, a
generator that derives ChatGPT/Office365 outputs from it, docs for authoring and for
consuming a skill on each platform, and one fully worked example skill.

**Architecture:** Skills are authored once under `skills/<slug>/SKILL.md` using Claude's
native skill frontmatter (`name`, `description`) plus extra fields (`category`, `audience`,
`mcp_tools`) that Claude ignores but the generator reads. `tools/generate-platforms.mjs`
reads every skill and writes adapted, checked-in outputs to `platforms/chatgpt/<slug>/` and
`platforms/office365/<slug>/`. Claude and Claude Code consume `skills/` directly with no
generation step.

**Tech Stack:** Plain Node.js (ESM modules), Node's built-in `node:test` runner — no
external npm dependencies anywhere in this repo.

Spec: `docs/superpowers/specs/2026-09-14-ai-skills-library-design.md`

---

### Task 1: Frontmatter parser

**Files:**
- Create: `tools/lib/frontmatter.mjs`
- Test: `tools/lib/frontmatter.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `tools/lib/frontmatter.test.mjs`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseFrontmatter } from './frontmatter.mjs';

test('parses scalar fields and a list field', () => {
  const content = `---
name: example-skill
description: Does a thing.
category: prospecting
audience: producer
mcp_tools:
  - tool_one
  - tool_two
---

# Example Skill

Body text here.
`;

  const { data, body } = parseFrontmatter(content);

  assert.equal(data.name, 'example-skill');
  assert.equal(data.description, 'Does a thing.');
  assert.equal(data.category, 'prospecting');
  assert.equal(data.audience, 'producer');
  assert.deepEqual(data.mcp_tools, ['tool_one', 'tool_two']);
  assert.equal(body, '# Example Skill\n\nBody text here.');
});

test('throws when content does not start with a frontmatter delimiter', () => {
  assert.throws(() => parseFrontmatter('# no frontmatter here'), /frontmatter delimiter/);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run (from repo root): `node --test tools/lib/frontmatter.test.mjs`
Expected: FAIL — `frontmatter.mjs` does not exist yet (module not found).

- [ ] **Step 3: Write the implementation**

Create `tools/lib/frontmatter.mjs`:

```js
export function parseFrontmatter(content) {
  const lines = content.split(/\r?\n/);
  if (lines[0] !== '---') {
    throw new Error('Expected content to start with "---" frontmatter delimiter');
  }

  const data = {};
  let currentListKey = null;
  let i = 1;

  for (; i < lines.length; i++) {
    const line = lines[i];
    if (line === '---') {
      i++;
      break;
    }

    const listMatch = line.match(/^\s*-\s*(.+)$/);
    if (listMatch) {
      if (!currentListKey) {
        throw new Error(`Unexpected list item outside of a list key: "${line}"`);
      }
      data[currentListKey].push(listMatch[1].trim());
      continue;
    }

    const kvMatch = line.match(/^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$/);
    if (kvMatch) {
      const [, key, value] = kvMatch;
      if (value === '') {
        data[key] = [];
        currentListKey = key;
      } else {
        data[key] = value;
        currentListKey = null;
      }
      continue;
    }

    if (line.trim() === '') {
      continue;
    }

    throw new Error(`Could not parse frontmatter line: "${line}"`);
  }

  const body = lines.slice(i).join('\n').trim();
  return { data, body };
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test tools/lib/frontmatter.test.mjs`
Expected: PASS, 2 tests passing.

- [ ] **Step 5: Commit**

```bash
git add tools/lib/frontmatter.mjs tools/lib/frontmatter.test.mjs
git commit -m "Add frontmatter parser for skill source files"
```

---

### Task 2: ChatGPT instructions renderer

**Files:**
- Create: `tools/lib/render-chatgpt.mjs`
- Test: `tools/lib/render-chatgpt.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `tools/lib/render-chatgpt.test.mjs`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderChatGptInstructions } from './render-chatgpt.mjs';

test('renders title, framing, body, and setup notes with mcp tools', () => {
  const output = renderChatGptInstructions({
    name: 'new-prospect-research-brief',
    description: 'Research a new prospect.',
    audience: 'producer',
    mcpTools: ['discovery_company_search', 'research_brief_generate'],
    body: '## Steps\n\n1. Do the thing.',
  });

  assert.match(output, /# New Prospect Research Brief/);
  assert.match(output, /You are a GPT that helps a producer with: Research a new prospect\./);
  assert.match(output, /## Steps\n\n1\. Do the thing\./);
  assert.match(output, /- discovery_company_search/);
  assert.match(output, /- research_brief_generate/);
});

test('uses "an" before a vowel-leading audience', () => {
  const output = renderChatGptInstructions({
    name: 'x',
    description: 'y.',
    audience: 'account manager',
    mcpTools: [],
    body: 'z',
  });

  assert.match(output, /helps an account manager with: y\./);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test tools/lib/render-chatgpt.test.mjs`
Expected: FAIL — `render-chatgpt.mjs` does not exist yet.

- [ ] **Step 3: Write the implementation**

Create `tools/lib/render-chatgpt.mjs`:

```js
function titleCase(slug) {
  return slug
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function article(word) {
  return /^[aeiou]/i.test(word) ? 'an' : 'a';
}

export function renderChatGptInstructions({ name, description, audience, mcpTools, body }) {
  const title = titleCase(name);
  const toolsList = mcpTools.map((tool) => `- ${tool}`).join('\n');

  return `# ${title} — ChatGPT Custom GPT Instructions

Paste the section below into this GPT's "Instructions" field.

## Instructions

You are a GPT that helps ${article(audience)} ${audience} with: ${description}

${body}

## Setup notes

This workflow was written against Zywave MCP tools, which ChatGPT does not call the same
way Claude does. Before this GPT can complete the workflow above, connect an Action or MCP
connector that provides equivalent capabilities for each of the following:

${toolsList}
`;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test tools/lib/render-chatgpt.test.mjs`
Expected: PASS, 2 tests passing.

- [ ] **Step 5: Commit**

```bash
git add tools/lib/render-chatgpt.mjs tools/lib/render-chatgpt.test.mjs
git commit -m "Add ChatGPT instructions renderer"
```

---

### Task 3: Office365 manifest + instructions renderer

**Files:**
- Create: `tools/lib/render-office365.mjs`
- Test: `tools/lib/render-office365.test.mjs`

- [ ] **Step 1: Write the failing test**

Create `tools/lib/render-office365.test.mjs`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { renderOffice365Manifest, renderOffice365Instructions } from './render-office365.mjs';

test('renders a manifest skeleton referencing instructions.md', () => {
  const manifest = renderOffice365Manifest({
    name: 'new-prospect-research-brief',
    description: 'Research a new prospect.',
  });

  assert.equal(manifest.name, 'New Prospect Research Brief');
  assert.equal(manifest.description, 'Research a new prospect.');
  assert.equal(manifest.instructions, 'instructions.md');
  assert.equal(manifest.version, 'v1.2');
});

test('renders instructions with body and setup notes', () => {
  const output = renderOffice365Instructions({
    name: 'new-prospect-research-brief',
    description: 'Research a new prospect.',
    audience: 'producer',
    mcpTools: ['discovery_company_search'],
    body: '## Steps\n\n1. Do the thing.',
  });

  assert.match(output, /# New Prospect Research Brief/);
  assert.match(output, /You are a declarative agent in Microsoft Copilot that helps a producer/);
  assert.match(output, /## Steps\n\n1\. Do the thing\./);
  assert.match(output, /- discovery_company_search/);
});
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `node --test tools/lib/render-office365.test.mjs`
Expected: FAIL — `render-office365.mjs` does not exist yet.

- [ ] **Step 3: Write the implementation**

Create `tools/lib/render-office365.mjs`:

```js
function titleCase(slug) {
  return slug
    .split('-')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function article(word) {
  return /^[aeiou]/i.test(word) ? 'an' : 'a';
}

export function renderOffice365Manifest({ name, description }) {
  return {
    '$schema': 'https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.2/schema.json',
    version: 'v1.2',
    name: titleCase(name),
    description,
    instructions: 'instructions.md',
  };
}

export function renderOffice365Instructions({ name, description, audience, mcpTools, body }) {
  const title = titleCase(name);
  const toolsList = mcpTools.map((tool) => `- ${tool}`).join('\n');

  return `# ${title} — Office365 Copilot Declarative Agent Instructions

Use this as the instructions file referenced by manifest.json for this declarative agent.

## Instructions

You are a declarative agent in Microsoft Copilot that helps ${article(audience)} ${audience} with: ${description}

${body}

## Setup notes

This workflow was written against Zywave MCP tools, which this declarative agent does not
call the same way Claude does. Before this agent can complete the workflow above, connect a
plugin or MCP connector that provides equivalent capabilities for each of the following:

${toolsList}
`;
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `node --test tools/lib/render-office365.test.mjs`
Expected: PASS, 2 tests passing.

- [ ] **Step 5: Commit**

```bash
git add tools/lib/render-office365.mjs tools/lib/render-office365.test.mjs
git commit -m "Add Office365 manifest and instructions renderer"
```

---

### Task 4: Generator script and package.json

**Files:**
- Create: `tools/generate-platforms.mjs`
- Create: `tools/package.json`

- [ ] **Step 1: Write `tools/package.json`**

```json
{
  "name": "zywave-skills-tools",
  "private": true,
  "type": "module",
  "scripts": {
    "generate": "node generate-platforms.mjs",
    "test": "node --test lib/*.test.mjs"
  }
}
```

> **Correction (discovered during Task 3's review):** `node --test lib/` (a bare directory
> path) fails with `MODULE_NOT_FOUND` on this Node v24 / Windows setup — it does not recurse
> into the directory to discover test files the way it does on some other platforms. The
> glob form `node --test lib/*.test.mjs` works correctly and is what's used above and in
> Step 3 below.

- [ ] **Step 2: Write `tools/generate-platforms.mjs`**

```js
import { readdirSync, readFileSync, mkdirSync, writeFileSync, statSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parseFrontmatter } from './lib/frontmatter.mjs';
import { renderChatGptInstructions } from './lib/render-chatgpt.mjs';
import { renderOffice365Manifest, renderOffice365Instructions } from './lib/render-office365.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = join(__dirname, '..');
const skillsDir = join(repoRoot, 'skills');
const platformsDir = join(repoRoot, 'platforms');

function listSkillSlugs() {
  return readdirSync(skillsDir).filter((entry) =>
    statSync(join(skillsDir, entry)).isDirectory()
  );
}

function loadSkill(slug) {
  const skillPath = join(skillsDir, slug, 'SKILL.md');
  const content = readFileSync(skillPath, 'utf8');
  const { data, body } = parseFrontmatter(content);
  return {
    name: data.name,
    description: data.description,
    audience: data.audience,
    mcpTools: data.mcp_tools ?? [],
    body,
  };
}

function generateChatGpt(slug, skill) {
  const outDir = join(platformsDir, 'chatgpt', slug);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(join(outDir, 'instructions.md'), renderChatGptInstructions(skill));
}

function generateOffice365(slug, skill) {
  const outDir = join(platformsDir, 'office365', slug);
  mkdirSync(outDir, { recursive: true });
  writeFileSync(
    join(outDir, 'manifest.json'),
    JSON.stringify(renderOffice365Manifest(skill), null, 2) + '\n'
  );
  writeFileSync(join(outDir, 'instructions.md'), renderOffice365Instructions(skill));
}

function main() {
  const slugs = listSkillSlugs();
  if (slugs.length === 0) {
    console.log('No skills found under skills/ — nothing to generate.');
    return;
  }
  for (const slug of slugs) {
    const skill = loadSkill(slug);
    generateChatGpt(slug, skill);
    generateOffice365(slug, skill);
    console.log(`Generated platform outputs for ${slug}`);
  }
}

main();
```

- [ ] **Step 3: Verify the renderer tests still pass from the new package location**

Run: `cd tools && npm test`
Expected: PASS, 6 tests passing — `node --test lib/*.test.mjs` picks up every `*.test.mjs`
under `tools/lib/`, so this re-runs Task 1's 2 frontmatter tests plus Task 2's 2 ChatGPT
tests plus Task 3's 2 Office365 tests (2 + 2 + 2 = 6). Confirm none failed.

- [ ] **Step 4: Commit**

```bash
cd ..
git add tools/generate-platforms.mjs tools/package.json
git commit -m "Add platform generator script"
```

---

### Task 5: Canonical example skill

**Files:**
- Create: `skills/new-prospect-research-brief/SKILL.md`

- [ ] **Step 1: Write the skill**

Create `skills/new-prospect-research-brief/SKILL.md`:

```markdown
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

# New Prospect Research Brief

## When to use this skill

Use this when a producer has a lead — a company or a household — that isn't yet a managed
account, and wants a research brief to prepare for first outreach.

## Steps

1. **Confirm what kind of prospect this is.** A business (has a company name) uses the
   company tools below; a household/individual uses the household tools.

2. **Find the prospect in Market Discovery.**
   - Company: call `discovery_company_search` with the company name (and location, if
     known, to narrow results). Company MSIDs start with `M`.
   - Household: call `discovery_household_search` with the name and location. Household
     MSIDs start with `H`.
   - If more than one plausible match comes back, show the candidates to the producer
     (name, location, any distinguishing detail) and ask which one before continuing.

3. **Pull the contacts.**
   - Company: call `discovery_company_contacts_get` with the MSID from step 2.
   - Household: call `discovery_household_contact_get` with the MSID from step 2.

4. **Generate the research brief.** Call `research_brief_generate` with the MSID. This
   returns a `publicId` immediately — the brief is not ready yet.

5. **Poll until the brief is ready.** Call `research_brief_get` with the `publicId` from
   step 4, repeating until `status` is `complete` or `failed`. Do not report to the producer
   until you've reached one of these two states.

6. **Present the result.**
   - If `complete`: summarize the brief for the producer, include the contacts from step 3,
     and suggest a next step (e.g. starting an outreach sequence with this MSID).
   - If `failed`: tell the producer the brief generation failed and offer to retry once,
     rather than silently giving up.

## Notes

- Don't confuse this with Account Management — this skill is for prospects that aren't in
  the producer's book of business yet. If the name the producer gives you turns out to
  already be a managed account, say so and suggest using account search instead.
- MSIDs from discovery can be passed directly to account tools later if this prospect
  converts into a client.
```

- [ ] **Step 2: Commit**

```bash
git add skills/new-prospect-research-brief/SKILL.md
git commit -m "Add new-prospect-research-brief example skill"
```

---

### Task 6: Generate and commit platform outputs

**Files:**
- Create: `platforms/chatgpt/new-prospect-research-brief/instructions.md` (generated)
- Create: `platforms/office365/new-prospect-research-brief/manifest.json` (generated)
- Create: `platforms/office365/new-prospect-research-brief/instructions.md` (generated)

- [ ] **Step 1: Run the generator**

Run: `cd tools && npm run generate`
Expected output: `Generated platform outputs for new-prospect-research-brief`

- [ ] **Step 2: Verify the generated ChatGPT file**

Read `platforms/chatgpt/new-prospect-research-brief/instructions.md` and confirm it
contains:
- Heading `# New Prospect Research Brief — ChatGPT Custom GPT Instructions`
- The line `You are a GPT that helps a producer with: Research a new company or household prospect and produce a research brief before outreach.`
- The full numbered Steps section from the skill body
- A "## Setup notes" section listing all six `mcp_tools` from Task 5

- [ ] **Step 3: Verify the generated Office365 files**

Read `platforms/office365/new-prospect-research-brief/manifest.json` and confirm it is
valid JSON with `name: "New Prospect Research Brief"` and `instructions: "instructions.md"`.

Read `platforms/office365/new-prospect-research-brief/instructions.md` and confirm it
contains the same Steps section and Setup notes list as the ChatGPT version, with the
"declarative agent in Microsoft Copilot" framing instead.

- [ ] **Step 4: Commit**

```bash
cd ..
git add platforms/
git commit -m "Generate ChatGPT and Office365 outputs for new-prospect-research-brief"
```

---

### Task 7: Authoring guide and platform notes docs

**Files:**
- Create: `docs/authoring-guide.md`
- Create: `docs/platform-notes/claude.md`
- Create: `docs/platform-notes/chatgpt.md`
- Create: `docs/platform-notes/office365.md`

- [ ] **Step 1: Write `docs/authoring-guide.md`**

`````markdown
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
`````

- [ ] **Step 2: Write `docs/platform-notes/claude.md`**

````markdown
# Using a skill in Claude / Claude Code

Claude's native skill format is the canonical format used in this repo — no conversion
needed.

## Claude Code

Copy (or symlink) the skill folder into your project's `.claude/skills/` directory:

```bash
cp -r skills/<slug> /path/to/your/project/.claude/skills/<slug>
```

Claude Code picks it up automatically; invoke it by name or let Claude select it based on
its `description`.

## claude.ai / Claude Desktop

Upload the skill folder (`skills/<slug>/`) through the Capabilities/Skills settings in
claude.ai or Claude Desktop. Claude reads the `name` and `description` frontmatter to decide
when to use it, and follows the body as instructions.

## Requirement

Every skill in this repo assumes the Zywave MCP server is connected. Without it, the MCP
tools listed in the skill's `mcp_tools` frontmatter aren't available and the skill can't
complete its steps.
````

- [ ] **Step 3: Write `docs/platform-notes/chatgpt.md`**

```markdown
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
```

- [ ] **Step 4: Write `docs/platform-notes/office365.md`**

```markdown
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
```

- [ ] **Step 5: Commit**

```bash
git add docs/authoring-guide.md docs/platform-notes/
git commit -m "Add authoring guide and per-platform usage docs"
```

---

### Task 8: Update root README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the contents of `README.md`**

````markdown
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
````

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "Rewrite README for the AI Skills library structure"
```

---

## Self-Review Notes (for whoever executes this plan)

- Spec coverage: repo layout (Task 1-8 collectively), canonical format (Task 5), generator
  (Tasks 1-4), example skill (Task 5-6), docs (Tasks 7-8) — all five spec sections have a
  task. The CI drift check was explicitly deferred in the spec and has no task here.
- Every code step above contains complete, runnable file content — no placeholders.
- Naming is consistent throughout: `mcpTools` (camelCase) in JS function parameters/renderer
  code, `mcp_tools` (snake_case) only in YAML frontmatter and the raw frontmatter parser's
  `data` object — the generator's `loadSkill` function is the single place that bridges
  `data.mcp_tools` to `mcpTools`.
