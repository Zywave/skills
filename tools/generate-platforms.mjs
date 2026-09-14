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
