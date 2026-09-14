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
