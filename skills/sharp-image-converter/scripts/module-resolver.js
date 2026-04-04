const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');
const { execSync } = require('child_process');

function collectRequireBases() {
  const bases = [];

  try {
    const globalRoot = execSync('npm root -g', {
      stdio: ['ignore', 'pipe', 'ignore'],
      encoding: 'utf8'
    }).trim();
    if (globalRoot) {
      bases.push(path.join(globalRoot, '__codex_global__.js'));
    }
  } catch (_) {
  }

  const nodePath = process.env.NODE_PATH;
  if (nodePath) {
    for (const entry of nodePath.split(path.delimiter)) {
      if (entry) {
        bases.push(path.join(entry, '__codex_node_path__.js'));
      }
    }
  }

  const cwdPkg = path.join(process.cwd(), 'package.json');
  if (fs.existsSync(cwdPkg)) {
    bases.push(cwdPkg);
  }

  bases.push(__filename);
  return bases;
}

function loadModule(moduleName) {
  const errors = [];

  for (const base of collectRequireBases()) {
    try {
      return createRequire(base)(moduleName);
    } catch (error) {
      errors.push(`${base}: ${error.code || error.message}`);
    }
  }

  const details = errors.map(line => `  - ${line}`).join('\n');
  throw new Error(
    `Could not load "${moduleName}". Checked these locations in order:\n${details}\n` +
    `Install it globally with: npm install -g ${moduleName}`
  );
}

module.exports = { loadModule };
