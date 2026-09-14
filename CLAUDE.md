# Repo notes for contributors

This file is for whoever works on the *generator tooling* in this repo. If you're authoring
a skill or consuming one on a platform, see `docs/authoring-guide.md` and
`docs/platform-notes/` instead — those are the actual deliverable docs.

## Architecture

- `skills/<slug>/SKILL.md` is the canonical, single source of truth per skill (Claude's
  native skill frontmatter + a markdown body). Claude and Claude Code consume it directly,
  no generation step.
- `tools/generate-platforms.mjs` reads every skill and derives `platforms/chatgpt/<slug>/`
  and `platforms/office365/<slug>/` from it. Those are generated and committed — never
  hand-edit them; edit the skill and regenerate instead.
- `tools/lib/frontmatter.mjs` parses a skill file into `{ data, body }`.
  `tools/lib/render-chatgpt.mjs` and `tools/lib/render-office365.mjs` render the two
  platform outputs from those parsed fields. Each renderer duplicates small
  `titleCase`/`article` helpers rather than sharing them — intentional at this scale (two
  renderers); worth extracting into a shared module only if a third platform renderer
  shows up.

## Working on the generator

- Run tests: `cd tools && npm test`
- Regenerate platform output after any skill or renderer change: `cd tools && npm run generate`,
  then commit `skills/` and `platforms/` together.
- No external npm dependencies anywhere in `tools/` — keep it that way. The frontmatter
  parser is a small hand-written subset of YAML (scalar `key: value` lines + one level of
  `key:` + indented `- item` lists), not a real YAML library.

## Known gotchas

- `node --test lib/` (a bare directory path) fails with `MODULE_NOT_FOUND` on Node v24 on
  Windows — it does not recurse into the directory to discover test files. Always use a
  glob instead: `node --test lib/*.test.mjs`. This is why `tools/package.json`'s `test`
  script is written that way.
- The frontmatter parser doesn't handle quoted scalar values, nested maps, or a missing
  closing `---` (a truncated file silently produces an empty body rather than erroring).
  Acceptable for the current controlled schema and single-skill scale; harden it if that
  ever becomes a real problem.
- The `category` frontmatter field is author-facing only (for browsing/grouping skills by
  eye) — it's parsed but **not** read by the generator or by Claude. If you add logic that
  depends on it, update `docs/authoring-guide.md`'s claim about what the generator reads
  accordingly.
