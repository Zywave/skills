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
