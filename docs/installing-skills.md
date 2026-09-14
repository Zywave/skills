# Installing Zywave Skills

Two ways to get these skills into an AI client: through that client's own desktop/web
app, or from a terminal. Both point at the same files in `skills/` — nothing here is a
different skill format per client, only a different install step.

## Desktop / web apps

### Claude — Desktop app

1. Open the Claude Desktop app.
2. Click the **+** button next to the prompt box → **Plugins** → **Add plugin** (or
   **Settings → Plugins**).
3. Choose **Add marketplace**, enter `Zywave/skills` (or
   `https://github.com/Zywave/skills`), and turn on **Sync automatically**.
4. Install the `zywave-skills` plugin. It bundles every skill in this repo, and updates
   automatically as skills here change.

This only works in local or SSH sessions of the Desktop app — not cloud/WSL sessions
(see "managed/cloud sessions" below for those).

### Claude — claude.ai (web browser)

claude.ai's web app doesn't have the plugin marketplace above — only per-skill upload,
and only for individual users (not org-wide, and admins can't manage it centrally):

1. Download this repo, or just the one skill folder you want (e.g.
   `skills/book-of-business-audit/`), and zip that folder.
2. In claude.ai, go to **Settings → Features** (also called Capabilities) and make sure
   code execution is enabled — requires a Pro, Max, Team, or Enterprise plan.
3. Upload the zip as a custom Skill.
4. Repeat per skill, per teammate — there's no bulk import on claude.ai today.

### Claude — managed/cloud sessions (team-wide)

An admin can pre-configure the Desktop app's marketplace for a whole team via
`extraKnownMarketplaces` + `enabledPlugins` in `.claude/settings.json`, instead of each
person adding it by hand.

### ChatGPT (web, desktop, mobile)

Individual users browse a public plugin directory — this repo isn't published there. For
a workspace to get everything in one step, a workspace admin imports it directly:

1. **Admin → Plugins → Add → Import marketplace**.
2. Enter the repo as the source: `https://github.com/Zywave/skills`.
3. ChatGPT reads `.agents/plugins/marketplace.json` at the repo root (added alongside this
   doc) and imports the plugin it lists.
4. It syncs automatically afterward, picking up new or edited skills.

### Gemini Enterprise (web console)

No GitHub import here — skills are added one at a time:

1. Go to **Skills** → the add icon → **Upload skill**.
2. Download the skill's `SKILL.md` from this repo — or, for a skill with a `scripts/` or
   `references/` folder, zip the whole `skills/<slug>/` folder instead.
3. Drag or browse to that file, then select **Import**.
4. Repeat per skill.

(Gemini CLI — the terminal tool — is a different product; see Terminal below.)

### Microsoft 365 Copilot (Cowork)

No admin setup or app package — it's a folder drop into OneDrive:

1. Open Microsoft 365 Copilot, switch to **Cowork**.
2. In your OneDrive, open (or create) `Documents/Cowork/skills/`.
3. Download the `skills/<slug>/` folder you want from this repo and copy it in, so
   `SKILL.md` and any `references/`/`scripts/` subfolders land inside
   `Documents/Cowork/skills/<slug>/`.
4. Cowork picks it up automatically at the start of your next conversation. (Limit: 50
   custom skills per profile.)

## Terminal

One command installs every skill in this repo into any of 49 supported clients — GitHub
Copilot, Cursor, OpenAI Codex, Gemini CLI, Claude Code, and more:

```
gh skill install Zywave/skills --all
```

Requires GitHub CLI v2.90.0+. Drop `--all` to pick specific skills interactively instead.
Claude Code also has its own equivalent:

```
/plugin marketplace add Zywave/skills
/plugin install zywave-skills@zywave-skills
```

See [`README.md`](../README.md#using-a-skill) for both.

## How confident is each of these

- **Claude Desktop, Claude Code, `gh skill install`:** confirmed against official docs,
  and the Desktop marketplace dialog was confirmed live against this exact repo.
- **ChatGPT's admin marketplace import:** confirmed against OpenAI's own help/developer
  docs, but not tested end-to-end against this repo.
- **Gemini Enterprise's upload flow and M365 Copilot Cowork's OneDrive folder-drop:**
  confirmed against Google's documentation and Microsoft/community documentation
  respectively, but not tested end-to-end against this repo.

If one of the less-certain steps doesn't match what you see in the product, that's this
doc to fix — the underlying `skills/<slug>/SKILL.md` files don't change per client.
