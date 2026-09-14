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
