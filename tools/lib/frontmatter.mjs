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
