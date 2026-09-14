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
