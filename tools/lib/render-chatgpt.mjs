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
