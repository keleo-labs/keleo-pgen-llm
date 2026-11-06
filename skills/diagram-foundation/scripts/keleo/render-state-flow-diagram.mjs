#!/usr/bin/env node
/**
 * Render an alpha's state model as a static SVG activity diagram.
 *
 * Most state models are ladders and draw as a plain left-to-right chain. Some are cycles:
 * a state may declare loopsBackTo, saying that reaching it means the concern is ready to go
 * round again rather than done (keleo-language semantics 6.8). That return is drawn as a
 * guarded edge out of a decision, routed through a channel below the chain.
 *
 * Split into a pure layout function and a renderer, mirroring render-orchestration-diagram.mjs
 * and the data/layout-module plus renderer split that specification/diagrams/README.md mandates,
 * so the layout body ports into the GAS navigator unchanged.
 *
 * Usage:
 *   node utils/render-state-flow-diagram.mjs <document.json> [alpha name] [options]
 *
 * Options:
 *   --out <path>   Write the SVG to a path (single alpha only).
 *   --outdir <dir> Directory for --all output. Default utils/out.
 *   --all          Render every alpha in the document that has states.
 *   --quiet        Suppress resolution warnings.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { esc, trunc, nameMaxChars, wrapLines, slug } from './diagram-text.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------

const PAD = 20;
const NODE_W = 150;
const NODE_H = 46;
const GAP = 30;
const START_R = 7;
const END_R = 9;
const DIAMOND_R = 14;
// The first return channel clears the node boxes; each loop below it takes another step, so a
// wider cycle can enclose a narrower one without the two edges sharing a line.
const CHANNEL_GAP = 28;
const CHANNEL_STEP = 30;
const DIVIDER_CAPTION_H = 18;
const TITLE_H = 42;

const COLOUR = {
  canvas: '#fafafa',
  card: '#ffffff',
  rule: '#d2d2d2',
  ink: '#151515',
  muted: '#6a6e73',
  edge: 'rgba(102,102,102,0.8)',
  loop: '#8476d1',
  loopWash: 'rgba(132,118,209,0.10)'
};

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

/** The table's state ramp, so the figure and the table below it read as one system. */
export function stateColour(index, total) {
  const span = Math.max(total - 1, 1);
  return `hsl(${210 + (index / span) * 90}, 70%, 50%)`;
}

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
// Loop resolution
// ---------------------------------------------------------------------------

/**
 * Resolve every loopsBackTo edge on a sorted state list against its siblings.
 *
 * An unresolvable edge is dropped with a warning rather than thrown: validate-practice.py is
 * what rejects bad data, and a viewer that refuses to draw a practice because one edge is
 * wrong is less useful than one that draws the ladder and says what it could not place.
 */
export function resolveStateLoops(sortedStates) {
  const states = sortedStates || [];
  const warnings = [];
  const loops = [];

  states.forEach((state, index) => {
    const loop = state.loopsBackTo;
    if (!loop) return;
    const targetIndex = states.findIndex((s) => s.name === loop.stateName);
    if (targetIndex === -1) {
      warnings.push(`State "${state.name}" loops back to "${loop.stateName}", which is not a state of this alpha — the edge is not drawn`);
      return;
    }
    if (targetIndex >= index) {
      warnings.push(`State "${state.name}" loops back to "${loop.stateName}", which does not come earlier in the sequence — the edge is not drawn`);
      return;
    }
    loops.push({
      fromName: state.name,
      fromIndex: index,
      toName: loop.stateName,
      toIndex: targetIndex,
      description: loop.description || '',
      condition: loop.condition || null,
      guard: guardLabel(loop)
    });
  });

  // The earliest loop target is where the recurring part of the model begins. Everything before
  // it is a one-time prefix: states a concern passes through once and never revisits.
  const entryIndex = loops.length ? Math.min(...loops.map((l) => l.toIndex)) : -1;

  return {
    loops,
    entryNames: loops.map((l) => l.toName),
    entryIndex,
    warnings
  };
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

/**
 * Lay out the chain, its decisions and its return edges.
 *
 * The chain keeps seq order, so the figure's columns line up with the state table underneath it.
 * A decision is placed after each state that closes a loop — that state has two futures, and the
 * guard says which is taken — rather than one decision for the whole alpha, so a model with two
 * cycles draws two.
 */
export function computeStateFlowLayout(sortedStates) {
  const states = sortedStates || [];
  const resolved = resolveStateLoops(states);
  const loopsByFromIndex = new Map(resolved.loops.map((l) => [l.fromIndex, l]));
  const hasLoop = resolved.loops.length > 0;
  const showDivider = resolved.entryIndex > 0;

  const nodeTop = PAD + (showDivider ? DIVIDER_CAPTION_H : 0);
  const cy = nodeTop + NODE_H / 2;
  const nodeBottom = nodeTop + NODE_H;

  let x = PAD;
  const start = { cx: x + START_R, cy, r: START_R };
  x += 2 * START_R + GAP;

  const nodes = [];
  const decisions = [];
  states.forEach((state, index) => {
    nodes.push({
      index,
      name: state.name,
      seq: state.seq,
      description: state.description || '',
      x,
      y: nodeTop,
      w: NODE_W,
      h: NODE_H,
      colour: stateColour(index, states.length),
      loops: loopsByFromIndex.has(index),
      loopEntry: resolved.entryNames.indexOf(state.name) !== -1,
      prefix: showDivider && index < resolved.entryIndex
    });
    x += NODE_W + GAP;
    const loop = loopsByFromIndex.get(index);
    if (loop) {
      decisions.push({ fromIndex: index, cx: x + DIAMOND_R, cy, r: DIAMOND_R });
      x += 2 * DIAMOND_R + GAP;
    }
  });

  const end = { cx: x + END_R, cy, r: END_R };
  x += 2 * END_R;

  // --- forward edges, each between whatever two items are adjacent in the chain -------------
  const chain = [{ right: start.cx + START_R }];
  nodes.forEach((n) => {
    chain.push({ left: n.x, right: n.x + n.w });
    const d = decisions.find((dd) => dd.fromIndex === n.index);
    if (d) chain.push({ left: d.cx - d.r, right: d.cx + d.r });
  });
  chain.push({ left: end.cx - END_R });

  const connectors = [];
  for (let i = 0; i < chain.length - 1; i++) {
    const x1 = chain[i].right;
    const x2 = chain[i + 1].left;
    connectors.push({ x1, y1: cy, x2, y2: cy, arrows: arrowLines(x2, cy, 1, 0, 7) });
  }

  // --- return edges, each in its own channel ------------------------------------------------
  // Widest span deepest, so a cycle that encloses another does not share its line.
  const ordered = [...resolved.loops].sort((a, b) => (a.fromIndex - a.toIndex) - (b.fromIndex - b.toIndex));
  const returns = ordered.map((loop, depth) => {
    const decision = decisions.find((d) => d.fromIndex === loop.fromIndex);
    const target = nodes[loop.toIndex];
    const channelY = nodeBottom + CHANNEL_GAP + depth * CHANNEL_STEP;
    const fromX = decision.cx;
    const toX = target.x + target.w / 2;
    return {
      ...loop,
      channelY,
      segments: [
        { x1: fromX, y1: decision.cy + decision.r, x2: fromX, y2: channelY },
        { x1: fromX, y1: channelY, x2: toX, y2: channelY },
        { x1: toX, y1: channelY, x2: toX, y2: target.y + target.h }
      ],
      arrows: arrowLines(toX, target.y + target.h, 0, -1, 7),
      label: { x: Math.min(fromX, toX), w: Math.abs(fromX - toX), y: channelY }
    };
  });

  // --- the one-time / recurring divider ------------------------------------------------------
  let divider = null;
  if (showDivider) {
    const before = nodes[resolved.entryIndex - 1];
    const after = nodes[resolved.entryIndex];
    const dx = (before.x + before.w + after.x) / 2;
    const deepest = returns.length ? returns[returns.length - 1].channelY : nodeBottom;
    divider = { x: dx, y1: nodeTop - DIVIDER_CAPTION_H + 4, y2: deepest + 10, captionY: nodeTop - 6 };
  }

  const deepest = returns.length ? returns[returns.length - 1].channelY : nodeBottom;
  const height = deepest + (returns.length ? 18 : 0) + PAD;

  return {
    width: x + PAD,
    height,
    nodeTop,
    nodeBottom,
    cy,
    start,
    nodes,
    decisions,
    end,
    connectors,
    returns,
    divider,
    hasLoop,
    warnings: resolved.warnings
  };
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

export function renderStaticSvg(layout, opts = {}) {
  const title = opts.title || '';
  const h = layout.height + (title ? TITLE_H : 0);
  const out = [];
  out.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${layout.width}" height="${h}" viewBox="0 0 ${layout.width} ${h}">`);
  out.push(`<rect width="${layout.width}" height="${h}" fill="${COLOUR.canvas}" rx="4"/>`);
  if (title) {
    out.push(textEl(PAD, 26, title, { size: 16, weight: 700 }));
    out.push(`<g transform="translate(0, ${TITLE_H})">`);
  }

  // Forward edges, under everything else
  for (const c of layout.connectors) {
    out.push(lineEl(c, COLOUR.edge, 1.5));
    for (const a of c.arrows) out.push(lineEl(a, COLOUR.edge, 1.5));
  }

  // Return edges and their guards
  for (const r of layout.returns) {
    for (const s of r.segments) out.push(lineEl(s, COLOUR.loop, 1.5));
    for (const a of r.arrows) out.push(lineEl(a, COLOUR.loop, 1.5));
    out.push(textEl(r.label.x + r.label.w / 2, r.label.y + 13, `[${trunc(r.guard, nameMaxChars(r.label.w))}]`, {
      size: 9, fill: COLOUR.loop, anchor: 'middle'
    }));
  }

  // The one-time / recurring divider
  if (layout.divider) {
    out.push(lineEl({ x1: layout.divider.x, y1: layout.divider.y1, x2: layout.divider.x, y2: layout.divider.y2 }, COLOUR.rule, 1, '3 3'));
    out.push(textEl(layout.divider.x - 6, layout.divider.captionY, 'one-time', { size: 9, fill: COLOUR.muted, anchor: 'end' }));
    out.push(textEl(layout.divider.x + 6, layout.divider.captionY, 'recurring', { size: 9, fill: COLOUR.muted }));
  }

  // Start marker
  out.push(`<circle cx="${layout.start.cx}" cy="${layout.start.cy}" r="${layout.start.r}" fill="${COLOUR.ink}"/>`);

  // State nodes
  for (const n of layout.nodes) {
    out.push(`<rect x="${n.x}" y="${n.y}" width="${n.w}" height="${n.h}" rx="6" fill="${COLOUR.card}" stroke="${COLOUR.rule}" stroke-width="1"/>`);
    out.push(`<circle cx="${n.x + 20}" cy="${n.y + n.h / 2}" r="11" fill="${n.colour}"/>`);
    out.push(textEl(n.x + 20, n.y + n.h / 2 + 4, String(n.seq), { size: 10, weight: 700, fill: '#ffffff', anchor: 'middle' }));
    const lines = wrapLines(n.name.replace(/-/g, '- '), nameMaxChars(n.w - 45), 2);
    const firstY = n.y + n.h / 2 + 4 - (lines.length - 1) * 6;
    lines.forEach((line, li) => {
      out.push(textEl(n.x + 37, firstY + li * 12, line, { size: 10, weight: 600 }));
    });
    if (n.loops) out.push(textEl(n.x + n.w - 6, n.y + 14, '↻', { size: 11, fill: COLOUR.loop, anchor: 'end' }));
  }

  // Decisions
  for (const d of layout.decisions) {
    out.push(
      `<path d="M ${d.cx} ${d.cy - d.r} L ${d.cx + d.r} ${d.cy} L ${d.cx} ${d.cy + d.r} L ${d.cx - d.r} ${d.cy} Z" ` +
      `fill="${COLOUR.loopWash}" stroke="${COLOUR.loop}" stroke-width="1.5"/>`
    );
  }

  // End marker
  out.push(`<circle cx="${layout.end.cx}" cy="${layout.end.cy}" r="${layout.end.r}" fill="none" stroke="${COLOUR.ink}" stroke-width="1.5"/>`);
  out.push(`<circle cx="${layout.end.cx}" cy="${layout.end.cy}" r="${layout.end.r - 4}" fill="${COLOUR.ink}"/>`);

  if (title) out.push('</g>');
  out.push('</svg>');
  return out.join('\n');
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  if (argv.includes('--help')) {
    console.log('Usage: node render-state-flow-diagram.mjs <document.json> [alpha name] [--all] [--out <path>] [--outdir <dir>] [--quiet]');
    process.exit(0);
  }
  const positional = [];
  const opts = { out: null, outdir: path.join(HERE, 'out'), all: false, quiet: false };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--all') opts.all = true;
    else if (arg === '--quiet') opts.quiet = true;
    else if (arg === '--out') opts.out = argv[++i];
    else if (arg === '--outdir') opts.outdir = argv[++i];
    else if (arg.startsWith('--')) throw new Error(`Unknown option: ${arg}`);
    else positional.push(arg);
  }
  if (!positional.length) {
    throw new Error('Usage: node utils/render-state-flow-diagram.mjs <document.json> [alpha name] [--all]');
  }
  opts.document = positional[0];
  opts.alpha = positional[1] || null;
  return opts;
}

function sortedStatesOf(alpha) {
  return [...(alpha.states || [])].sort((a, b) => (a.seq || 0) - (b.seq || 0));
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const doc = JSON.parse(fs.readFileSync(opts.document, 'utf8'));
  const withStates = (doc.alphas || []).filter((a) => (a.states || []).length);
  if (!withStates.length) throw new Error('Document declares no alpha with states');

  const targets = opts.all
    ? withStates
    : [opts.alpha ? withStates.find((a) => a.name === opts.alpha) : withStates[0]];
  if (targets.some((t) => !t)) throw new Error(`No alpha named "${opts.alpha}" with states in document`);

  for (const alpha of targets) {
    const layout = computeStateFlowLayout(sortedStatesOf(alpha));
    const svg = renderStaticSvg(layout, { title: alpha.name });
    const outPath = opts.out && targets.length === 1
      ? opts.out
      : path.join(opts.outdir, `state-flow-${slug(alpha.name)}.svg`);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, svg + '\n');
    const shape = layout.hasLoop
      ? `cycles (${layout.returns.map((r) => `${r.fromName} → ${r.toName}`).join(', ')})`
      : 'ladder';
    console.log(`${alpha.name}: ${layout.width}×${layout.height} ${shape} → ${outPath}`);
    if (!opts.quiet) {
      for (const w of layout.warnings) console.error(`  warning: ${w}`);
    }
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  main();
}
