/**
 * Text measurement and escaping shared by the static diagram renderers.
 *
 * The character-limit rules come from specification/diagrams/README.md, which asks every
 * diagram to size its labels the same way so that a name truncated in one figure is truncated
 * at the same point in another. Three renderers now need them, which is what moved these out
 * of the first one that had them.
 */

export function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

export function trunc(s, maxChars) {
  const str = String(s == null ? '' : s);
  if (maxChars <= 1 || str.length <= maxChars) return str;
  return str.slice(0, Math.max(1, maxChars - 1)) + '…';
}

/** How many characters of a name fit in a box of this content width. */
export function nameMaxChars(contentWidth) {
  return Math.max(3, Math.floor(contentWidth / 8));
}

/** Descriptions are set smaller than names, so more of one fits in the same width. */
export function descMaxChars(contentWidth) {
  return Math.max(3, Math.floor(contentWidth / 6));
}

/**
 * Split on word boundaries to at most maxLines, truncating the last line. The navigator lets
 * text wrap inside a div, so this exists only to keep the static render honest about what fits.
 */
export function wrapLines(text, maxChars, maxLines) {
  const words = String(text == null ? '' : text).split(/\s+/).filter(Boolean);
  const lines = [];
  let current = '';
  for (const word of words) {
    const candidate = current ? `${current} ${word}` : word;
    if (candidate.length <= maxChars || !current) {
      current = candidate;
    } else {
      lines.push(current);
      current = word;
      if (lines.length === maxLines) break;
    }
  }
  if (lines.length < maxLines && current) lines.push(current);
  if (!lines.length) return [''];
  lines[lines.length - 1] = trunc(lines[lines.length - 1], maxChars);
  return lines;
}

export function slug(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}
