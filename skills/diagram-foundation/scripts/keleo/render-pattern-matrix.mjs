#!/usr/bin/env node
/**
 * Render a Pattern as a static SVG matrix: phases across, concerns down.
 *
 * A pattern view is the atomic column unit -- the same organising idea the orchestration
 * timeline is built on, where a stage occupies as many columns as its pattern has views. Here
 * those columns carry the alphas underneath them, so a phase is read down and a concern's
 * progression is read across.
 *
 * Views as columns is also what makes loopsBackTo drawable. The language specifies the shape:
 * "an arc from a later column back to an earlier one in the pattern matrix" (semantics 9.2a).
 * The arc runs in a channel between the headers and the grid, where it stays next to the
 * phases it spans however tall the grid below it grows.
 *
 * Split into a pure layout function and a renderer, mirroring render-orchestration-diagram.mjs
 * and render-state-flow-diagram.mjs, so the layout body ports into the GAS navigator unchanged.
 * The one exception is orderRows: the navigator substitutes NavigatorUtils.groupByFocus and
 * NavigatorHelpers.buildAlphaTree, which already do this and are already tested there.
 *
 * Usage:
 *   node utils/render-pattern-matrix.mjs <document.json> [pattern name] [options]
 *
 * Options:
 *   --out <path>   Write the SVG to a path (single pattern only).
 *   --outdir <dir> Directory for --all output. Default utils/out.
 *   --all          Render every pattern in the document.
 *   --quiet        Suppress resolution warnings.
 *   --note-offset <n> Continue note numbers when rendering a later excerpt.
 *   --title <text> Label an excerpt without renaming the source pattern.
 *   --external-loop-part <text> Draw a return to a phase in another panel.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { esc, trunc, nameMaxChars, descMaxChars, wrapLines, slug } from './diagram-text.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------

const PAD = 20;
const LABEL_W = 210;
const COL_W = 150;
const HEADER_H = 48;
const ROW_H = 30;
const STATE_H = 22;
const FOCUS_H = 24;
const BAND_GAP = 12;
const NARRATIVE_H = 20;
const NARRATIVE_GAP = 4;
// The first return channel clears the headers; each further loop takes another step, so a
// wider cycle can enclose a narrower one without the two edges sharing a line.
const LOOP_GAP = 24;
const LOOP_STEP = 30;
const LOOP_LABEL_H = 14;
const INDENT_W = 14;
const TITLE_H = 42;

const COLOUR = {
  canvas: '#fafafa',
  card: '#ffffff',
  rule: '#d2d2d2',
  ruleFaint: '#e8e8e8',
  ink: '#151515',
  muted: '#6a6e73',
  faint: '#adb5bd',
  spine: '#0066cc',
  spineWash: 'rgba(0,102,204,0.06)',
  narrativeWash: 'rgba(0,102,204,0.06)',
  carriedWash: '#f7f7f7',
  loop: '#8476d1',
  loopWash: 'rgba(132,118,209,0.10)'
};

// ---------------------------------------------------------------------------
// Reading the pattern
// ---------------------------------------------------------------------------

/**
 * A view's alphaStates are canonically {alphaName, stateName} objects, but the language still
 * accepts "Alpha→State" tokens from legacy interchange, so every read goes through here.
 */
function statesFor(view, alphaName) {
  const out = [];
  for (const as of view.alphaStates || []) {
    let a, s;
    if (typeof as === 'string') {
      const parts = as.split(/→|->/);
      a = (parts[0] || '').trim();
      s = (parts[1] || '').trim();
    } else {
      a = as.alphaName;
      s = as.stateName;
    }
    if (a === alphaName && s) out.push(s);
  }
  return out;
}

function referencedAlphaNames(views) {
  const names = [];
  const seen = new Set();
  for (const view of views) {
    for (const as of view.alphaStates || []) {
      const name = typeof as === 'string' ? (as.split(/→|->/)[0] || '').trim() : as.alphaName;
      if (name && !seen.has(name)) { seen.add(name); names.push(name); }
    }
  }
  return names;
}

/**
 * Rows, grouped into focus bands, roots before the contributors that feed them.
 *
 * A contributor whose root is absent from the pattern -- or sits in another focus -- becomes a
 * root of its own band, which is the behaviour the navigator's alpha tree already has.
 */
function orderRows(doc, referenced) {
  const alphaByName = new Map((doc.alphas || []).map((a) => [a.name, a]));
  const present = new Set(referenced);
  const parentOf = (alpha) => {
    const p = alpha.mapsTo || alpha.contributesTo;
    return p && present.has(p) ? p : null;
  };

  const focusOrder = (doc.focuses || []).map((f) => f.name);
  const bands = new Map();
  // Baseline declaration order within a band, not the order the pattern happens to mention
  // them in, so a concern sits in the same place here as it does in the navigator's sidebar.
  const inBandOrder = (doc.alphas || []).map((a) => a.name).filter((n) => present.has(n));
  for (const name of inBandOrder.concat(referenced.filter((n) => !alphaByName.has(n)))) {
    const alpha = alphaByName.get(name);
    const focusName = (alpha && alpha.focusName) || 'Other';
    if (!bands.has(focusName)) bands.set(focusName, []);
    bands.get(focusName).push(name);
  }

  const ordered = [...bands.keys()].sort((a, b) => {
    const ai = focusOrder.indexOf(a);
    const bi = focusOrder.indexOf(b);
    return (ai === -1 ? focusOrder.length : ai) - (bi === -1 ? focusOrder.length : bi);
  });

  return ordered.map((focusName) => {
    const members = bands.get(focusName);
    const inBand = new Set(members);
    const rows = [];
    const walk = (parentName, depth) => {
      for (const name of members) {
        const alpha = alphaByName.get(name);
        const parent = alpha ? parentOf(alpha) : null;
        // A parent outside this band cannot indent a row that is drawn inside it.
        const effective = parent && inBand.has(parent) ? parent : null;
        if (effective !== parentName) continue;
        rows.push({ alphaName: name, alpha: alpha || { name }, depth });
        walk(name, depth + 1);
      }
    };
    walk(null, 0);
    return { focusName, rows };
  });
}

/** What to write on the return edge: when the loop is taken rather than exited. */
function guardLabel(loop) {
  const condition = loop.condition || {};
  if (condition.name) return condition.name;
  if (condition.when && condition.when.length) return condition.when[0];
  return loop.description || 'repeats';
}

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

export function computePatternMatrixLayout(doc, patternName, deps = {}) {
  const warnings = [];
  const patterns = doc.patterns || [];
  const pattern = patternName
    ? patterns.find((p) => p.name === patternName)
    : patterns[0];
  if (!pattern) throw new Error(`No pattern named "${patternName}" in document`);

  const views = [...(pattern.patternViews || [])].sort((a, b) => (a.seq || 0) - (b.seq || 0));
  const referenced = referencedAlphaNames(views);
  const bands = (deps.orderRows || orderRows)(doc, referenced);

  // --- footnotes, numbered in reading order --------------------------------
  const footnotes = [];
  const noteFor = (kind, label, text) => {
    if (!text) return null;
    const num = (deps.noteOffset || 0) + footnotes.length + 1;
    footnotes.push({ num, kind, label, text });
    return num;
  };

  // --- columns -------------------------------------------------------------
  const columns = views.map((view, index) => ({
    index,
    name: view.name,
    seq: view.seq,
    description: view.description || '',
    x: PAD + LABEL_W + index * COL_W,
    w: COL_W,
    view
  }));
  const columnByName = new Map(columns.map((c) => [c.name, c]));

  // --- vertical cursor -----------------------------------------------------
  let y = PAD;

  // --- narrative strips, packed into rows ----------------------------------
  const narrativeType = (doc.narrativeTypes || []).find((n) => n.name === pattern.narrativeTypeName);
  if (pattern.narrativeTypeName && !narrativeType) {
    warnings.push(`Pattern declares narrativeTypeName "${pattern.narrativeTypeName}" but no such NarrativeType is in scope`);
  }
  const narrativeRows = [];
  if (narrativeType && columns.length) {
    const elements = [...(narrativeType.narrativeElements || [])].sort((a, b) => (a.seq || 0) - (b.seq || 0));
    for (const el of elements) {
      const hit = columns.filter((c) =>
        (c.view.narrativeContexts || []).some((nc) => nc.narrativeElementName === el.name)
      );
      if (!hit.length) continue;
      const left = Math.min(...hit.map((c) => c.x));
      const right = Math.max(...hit.map((c) => c.x + c.w));
      const strip = { label: el.name, x: left, w: right - left };
      let row = narrativeRows.find((r) => r.every((s) => s.x + s.w <= strip.x || strip.x + strip.w <= s.x));
      if (!row) { row = []; narrativeRows.push(row); }
      row.push(strip);
    }
  }
  const narrativeStrips = [];
  narrativeRows.forEach((row, ri) => {
    for (const s of row) {
      narrativeStrips.push({ ...s, y: y + ri * (NARRATIVE_H + NARRATIVE_GAP), h: NARRATIVE_H });
    }
  });
  if (narrativeRows.length) {
    y += narrativeRows.length * NARRATIVE_H + (narrativeRows.length - 1) * NARRATIVE_GAP + BAND_GAP;
  }

  // --- column headers ------------------------------------------------------
  const headerY = y;
  const headerBottom = y + HEADER_H;
  for (const c of columns) {
    c.y = headerY;
    c.h = HEADER_H;
    // The narrative context is a paragraph; the header carries a glyph and the text goes below
    // the figure, the same split the orchestration makes for its entry and exit criteria.
    const ctx = (c.view.narrativeContexts || [])[0];
    c.note = ctx ? noteFor('narrative', `${c.name} · ${ctx.narrativeElementName || 'Narrative'}`, ctx.context) : null;
  }
  y = headerBottom;

  // --- loop channels -------------------------------------------------------
  const loops = [];
  views.forEach((view, index) => {
    const loop = view.loopsBackTo;
    if (!loop) return;
    const targetIndex = views.findIndex((v) => v.name === loop.patternViewName);
    if (targetIndex === -1 && !deps.externalLoopPart) {
      warnings.push(`View "${view.name}" loops back to "${loop.patternViewName}", which is not a view of this pattern — the edge is not drawn`);
      return;
    }
    if (targetIndex >= index) {
      warnings.push(`View "${view.name}" loops back to "${loop.patternViewName}", which does not come earlier in the sequence — the edge is not drawn`);
      return;
    }
    loops.push({
      fromName: view.name,
      fromIndex: index,
      toName: loop.patternViewName,
      toIndex: targetIndex,
      externalPart: targetIndex === -1 ? deps.externalLoopPart : null,
      description: loop.description || '',
      condition: loop.condition || null,
      guard: guardLabel(loop)
    });
  });

  // Widest span deepest, so a cycle that encloses another does not share its line.
  const ordered = [...loops].sort((a, b) => (a.fromIndex - a.toIndex) - (b.fromIndex - b.toIndex));
  const loopEdges = ordered.map((loop, depth) => {
    const from = columns[loop.fromIndex];
    const to = columns[loop.toIndex];
    const channelY = headerBottom + LOOP_GAP + depth * LOOP_STEP;
    const fromX = from.x + from.w / 2;
    const toX = to ? to.x + to.w / 2 : PAD + LABEL_W - 12;
    const condition = loop.condition;
    const text = condition
      ? [(condition.given || [])[0], (condition.when || [])[0], (condition.then || [])[0]]
          .filter(Boolean).join(' · ') || condition.description || loop.description
      : loop.description;
    return {
      ...loop,
      channelY,
      segments: [
        { x1: fromX, y1: headerBottom, x2: fromX, y2: channelY },
        { x1: fromX, y1: channelY, x2: toX, y2: channelY },
        ...(to ? [{ x1: toX, y1: channelY, x2: toX, y2: headerBottom }] : [])
      ],
      arrows: to ? arrowLines(toX, headerBottom, 0, -1, 7) : arrowLines(toX, channelY, -1, 0, 7),
      label: { x: Math.min(fromX, toX), w: Math.abs(fromX - toX), y: channelY },
      note: noteFor('loop', `${loop.fromName} → ${loop.toName}`, text)
    };
  });
  if (loopEdges.length) {
    y = loopEdges[loopEdges.length - 1].channelY + LOOP_LABEL_H + BAND_GAP;
  } else {
    y += BAND_GAP / 2;
  }

  // --- the grid ------------------------------------------------------------
  const gridTop = y;
  const focusBands = [];
  const rows = [];
  const cells = [];
  const multiFocus = bands.length > 1;

  for (const band of bands) {
    if (multiFocus) {
      focusBands.push({ name: band.focusName, y, h: FOCUS_H, x: PAD, w: LABEL_W + columns.length * COL_W });
      y += FOCUS_H;
    }
    for (const row of band.rows) {
      const perColumn = columns.map((c) => statesFor(c.view, row.alphaName));
      const maxStates = Math.max(1, ...perColumn.map((s) => s.length));
      const h = Math.max(ROW_H, maxStates * STATE_H + 8);
      const rowRecord = {
        alphaName: row.alphaName,
        focusName: band.focusName,
        depth: row.depth,
        y,
        h,
        labelX: PAD + row.depth * INDENT_W,
        labelW: LABEL_W - row.depth * INDENT_W - 8
      };
      rows.push(rowRecord);

      // A state repeated from the previous column is carried over, not new work. It is muted
      // rather than dropped: semantics 9.2a.1 requires a re-entered view to show what the
      // iteration works on even where the state is unchanged.
      let lastDeclared = null;
      perColumn.forEach((states, ci) => {
        const column = columns[ci];
        if (!states.length) {
          cells.push({ alphaName: row.alphaName, viewName: column.name, x: column.x, y, w: COL_W, h, absent: true, states: [] });
          return;
        }
        const carried = states.length === 1 && states[0] === lastDeclared;
        cells.push({
          alphaName: row.alphaName,
          viewName: column.name,
          x: column.x,
          y,
          w: COL_W,
          h,
          absent: false,
          carried,
          states
        });
        lastDeclared = states[states.length - 1];
      });
      y += h;
    }
  }

  const gridBottom = y;
  const width = PAD + LABEL_W + columns.length * COL_W + PAD;

  return {
    name: pattern.name,
    description: pattern.description || '',
    narrativeTypeName: pattern.narrativeTypeName || null,
    width,
    height: gridBottom + PAD,
    labelW: LABEL_W,
    headerY,
    headerBottom,
    gridTop,
    gridBottom,
    columns,
    rows,
    focusBands,
    cells,
    narrativeStrips,
    loops: loopEdges,
    footnotes,
    warnings
  };
}

/** Arrowheads are two short lines, the same construction the other two figures use. */
function arrowLines(x2, y2, dx, dy, size) {
  const len = Math.sqrt(dx * dx + dy * dy);
  if (len === 0) return [];
  const ux = dx / len;
  const uy = dy / len;
  const px = -uy;
  const py = ux;
  return [
    { x1: x2, y1: y2, x2: x2 - ux * size + px * size * 0.45, y2: y2 - uy * size + py * size * 0.45 },
    { x1: x2, y1: y2, x2: x2 - ux * size - px * size * 0.45, y2: y2 - uy * size - py * size * 0.45 }
  ];
}

// ---------------------------------------------------------------------------
// Static SVG renderer
// ---------------------------------------------------------------------------

function textEl(x, y, str, opts = {}) {
  const size = opts.size || 10;
  const weight = opts.weight ? ` font-weight="${opts.weight}"` : '';
  const fill = opts.fill || COLOUR.ink;
  const anchor = opts.anchor ? ` text-anchor="${opts.anchor}"` : '';
  const extra = opts.letterSpacing ? ` letter-spacing="${opts.letterSpacing}"` : '';
  return `<text x="${x}" y="${y}" font-family="sans-serif" font-size="${size}"${weight} fill="${fill}"${anchor}${extra}>${esc(str)}</text>`;
}

function lineEl(l, colour, width, dash) {
  const d = dash ? ` stroke-dasharray="${dash}"` : '';
  return `<line x1="${l.x1}" y1="${l.y1}" x2="${l.x2}" y2="${l.y2}" stroke="${colour}" stroke-width="${width}"${d}/>`;
}

function noteGlyph(cx, cy, num, colour) {
  return (
    `<circle cx="${cx}" cy="${cy}" r="6.5" fill="${COLOUR.card}" stroke="${colour}" stroke-width="1"/>` +
    textEl(cx, cy + 3, String(num), { size: 8, weight: 600, fill: COLOUR.muted, anchor: 'middle' })
  );
}

export function renderStaticSvg(layout, opts = {}) {
  const title = opts.title === undefined ? layout.name : opts.title;
  const footH = layout.footnotes.length ? 20 + layout.footnotes.length * 15 : 0;
  const h = layout.height + (title ? TITLE_H : 0) + footH;
  const out = [];
  out.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${layout.width}" height="${h}" viewBox="0 0 ${layout.width} ${h}">`);
  out.push(`<rect width="${layout.width}" height="${h}" fill="${COLOUR.canvas}" rx="4"/>`);
  if (title) {
    out.push(textEl(PAD, 26, title, { size: 16, weight: 700 }));
    if (layout.description) {
      out.push(textEl(PAD, 40, trunc(layout.description, descMaxChars(layout.width - 2 * PAD)), { size: 10, fill: COLOUR.muted }));
    }
    out.push(`<g transform="translate(0, ${TITLE_H})">`);
  }

  // Narrative band
  for (const s of layout.narrativeStrips) {
    out.push(`<rect x="${s.x}" y="${s.y}" width="${s.w}" height="${s.h}" rx="3" fill="${COLOUR.narrativeWash}" stroke="${COLOUR.ruleFaint}" stroke-width="0.5"/>`);
    out.push(textEl(s.x + 8, s.y + 14, s.label.toUpperCase(), { size: 9, weight: 600, fill: COLOUR.muted, letterSpacing: '0.08em' }));
  }

  // Column headers
  for (const c of layout.columns) {
    out.push(`<rect x="${c.x + 1}" y="${c.y}" width="${c.w - 2}" height="${c.h}" rx="4" fill="${COLOUR.spineWash}" stroke="${COLOUR.spine}" stroke-width="1"/>`);
    const nameLines = wrapLines(c.name, nameMaxChars(c.w - 16), 2);
    nameLines.forEach((line, li) => {
      out.push(textEl(c.x + 8, c.y + 15 + li * 12, line, { size: 10, weight: 600 }));
    });
    if (c.description && nameLines.length === 1) {
      const descLines = wrapLines(c.description, descMaxChars(c.w - 16), 2);
      descLines.forEach((line, li) => {
        out.push(textEl(c.x + 8, c.y + 29 + li * 10, line, { size: 8, fill: COLOUR.muted }));
      });
    }
    if (c.note) out.push(noteGlyph(c.x + c.w - 12, c.y + 12, c.note, COLOUR.spine));
  }

  // Loop channels
  for (const edge of layout.loops) {
    for (const s of edge.segments) out.push(lineEl(s, COLOUR.loop, 1.5));
    for (const a of edge.arrows) out.push(lineEl(a, COLOUR.loop, 1.5));
    const returnTarget = edge.externalPart ? ` → ${edge.toName} (${edge.externalPart})` : '';
    const label = `[${trunc(edge.guard, nameMaxChars(edge.label.w))}]${returnTarget}`;
    out.push(textEl(edge.label.x + edge.label.w / 2, edge.label.y + 12, label, {
      size: 9, fill: COLOUR.loop, anchor: 'middle'
    }));
    if (edge.note) out.push(noteGlyph(edge.label.x + edge.label.w / 2 + 6 + label.length * 2.4, edge.label.y + 9, edge.note, COLOUR.loop));
  }

  // Focus bands
  for (const band of layout.focusBands) {
    out.push(`<rect x="${band.x}" y="${band.y}" width="${band.w}" height="${band.h}" fill="${COLOUR.carriedWash}"/>`);
    out.push(textEl(band.x + 6, band.y + 16, band.name.toUpperCase(), { size: 9, weight: 600, fill: COLOUR.muted, letterSpacing: '0.08em' }));
  }

  // Row labels
  for (const row of layout.rows) {
    const prefix = row.depth ? '└ ' : '';
    out.push(textEl(row.labelX + 6, row.y + 18, prefix + trunc(row.alphaName, nameMaxChars(row.labelW)), {
      size: 10, weight: row.depth ? 400 : 600, fill: row.depth ? COLOUR.muted : COLOUR.ink
    }));
    out.push(lineEl({ x1: PAD, y1: row.y, x2: layout.width - PAD, y2: row.y }, COLOUR.ruleFaint, 0.5));
  }

  // Cells
  for (const cell of layout.cells) {
    if (cell.absent) {
      out.push(textEl(cell.x + cell.w / 2, cell.y + 18, '·', { size: 10, fill: COLOUR.faint, anchor: 'middle' }));
      continue;
    }
    cell.states.forEach((state, si) => {
      const sy = cell.y + 4 + si * STATE_H;
      out.push(`<rect x="${cell.x + 4}" y="${sy}" width="${cell.w - 8}" height="${STATE_H - 4}" rx="9" fill="${cell.carried ? COLOUR.carriedWash : COLOUR.card}" stroke="${cell.carried ? COLOUR.ruleFaint : COLOUR.rule}" stroke-width="1"/>`);
      out.push(textEl(cell.x + cell.w / 2, sy + 12, trunc(state, nameMaxChars(cell.w - 16)), {
        size: 9, fill: cell.carried ? COLOUR.faint : COLOUR.ink, anchor: 'middle'
      }));
    });
  }

  // Column rules, over the grid so the columns read as columns
  for (const c of layout.columns) {
    out.push(lineEl({ x1: c.x, y1: layout.gridTop, x2: c.x, y2: layout.gridBottom }, COLOUR.ruleFaint, 0.5));
  }
  out.push(lineEl({ x1: PAD, y1: layout.gridBottom, x2: layout.width - PAD, y2: layout.gridBottom }, COLOUR.rule, 1));

  // Footnotes
  if (layout.footnotes.length) {
    let fy = layout.gridBottom + 24;
    for (const f of layout.footnotes) {
      out.push(noteGlyph(PAD + 7, fy - 4, f.num, f.kind === 'loop' ? COLOUR.loop : COLOUR.spine));
      out.push(textEl(PAD + 20, fy, `${f.label}: ${trunc(f.text, descMaxChars(layout.width - PAD - 40))}`, { size: 9, fill: COLOUR.muted }));
      fy += 15;
    }
  }

  if (title) out.push('</g>');
  out.push('</svg>');
  return out.join('\n');
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const positional = [];
  const opts = { out: null, outdir: path.join(HERE, 'out'), all: false, quiet: false, noteOffset: 0, title: null, externalLoopPart: null };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--all') opts.all = true;
    else if (arg === '--quiet') opts.quiet = true;
    else if (arg === '--out') opts.out = argv[++i];
    else if (arg === '--outdir') opts.outdir = argv[++i];
    else if (arg === '--title') opts.title = argv[++i];
    else if (arg === '--external-loop-part') opts.externalLoopPart = argv[++i];
    else if (arg === '--note-offset') {
      opts.noteOffset = Number(argv[++i]);
      if (!Number.isInteger(opts.noteOffset) || opts.noteOffset < 0) throw new Error('--note-offset requires a non-negative integer');
    }
    else if (arg.startsWith('--')) throw new Error(`Unknown option: ${arg}`);
    else positional.push(arg);
  }
  if (!positional.length) {
    throw new Error('Usage: node utils/render-pattern-matrix.mjs <document.json> [pattern name] [--all]');
  }
  opts.document = positional[0];
  opts.pattern = positional[1] || null;
  return opts;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const doc = JSON.parse(fs.readFileSync(opts.document, 'utf8'));
  const all = (doc.patterns || []).filter((p) => (p.patternViews || []).length);
  if (!all.length) throw new Error('Document declares no pattern with views');

  const targets = opts.all ? all.map((p) => p.name) : [opts.pattern || all[0].name];

  for (const name of targets) {
    const layout = computePatternMatrixLayout(doc, name, { noteOffset: opts.noteOffset, externalLoopPart: opts.externalLoopPart });
    const svg = renderStaticSvg(layout, { title: opts.title || undefined });
    const outPath = opts.out && targets.length === 1
      ? opts.out
      : path.join(opts.outdir, `pattern-matrix-${slug(name)}.svg`);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, svg + '\n');
    const loops = layout.loops.length
      ? ` loops (${layout.loops.map((l) => `${l.fromName} → ${l.toName}`).join(', ')})`
      : '';
    console.log(`${name}: ${layout.columns.length} views × ${layout.rows.length} concerns, ${layout.width}×${layout.height}${loops} → ${outPath}`);
    if (!opts.quiet) {
      for (const w of layout.warnings) console.error(`  warning: ${w}`);
    }
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  main();
}
