#!/usr/bin/env node
// Version: 1.0.0
// Inline local Markdown images for document import; rasterise SVG with sharp.
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require('sharp');

async function main() {
  const [source, output] = process.argv.slice(2);
  if (!source || !output) {
    console.error('Usage: node utils/prepare-markdown-images.js INPUT.md OUTPUT.md');
    process.exitCode = 2;
    return;
  }

  const markdown = await fs.readFile(source, 'utf8');
  let prepared = '';
  let end = 0;
  for (const match of markdown.matchAll(/!\[([^\]]*)\]\(([^)]+)\)/g)) {
    prepared += markdown.slice(end, match.index);
    const target = match[2];
    if (/^(?:https?:|data:)/.test(target)) {
      prepared += match[0];
    } else {
      const extension = path.extname(target).toLowerCase();
      const data = await fs.readFile(path.resolve(path.dirname(source), target));
      const image = extension === '.svg' ? await sharp(data).resize({ width: 600 }).png().toBuffer() : data;
      const mime = extension === '.svg' || extension === '.png' ? 'image/png' : extension === '.jpg' || extension === '.jpeg' ? 'image/jpeg' : null;
      if (!mime) throw new Error(`Unsupported image type: ${target}`);
      prepared += `![${match[1]}](data:${mime};base64,${image.toString('base64')})`;
    }
    end = match.index + match[0].length;
  }
  await fs.writeFile(output, prepared + markdown.slice(end));
  console.log(`Prepared ${output}`);
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
