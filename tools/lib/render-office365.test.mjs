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
