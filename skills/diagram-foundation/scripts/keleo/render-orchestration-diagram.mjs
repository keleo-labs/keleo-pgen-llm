#!/usr/bin/env node
/**
 * Render a schema 3.0.0 PatternOrchestration as a static SVG layered timeline.
 *
 * Split into a pure layout function and a renderer, mirroring the data/layout-module plus
 * renderer split that specification/diagrams/README.md mandates for the other seven diagram
 * types, so both bodies port into the GAS navigator and the keleo-studio static export.
 *
 * The organising idea: a pattern view is the atomic column unit. Every sequential stage
 * occupies as many columns as its pattern has views, and concurrent, nested and scoped
 * stages position against those columns, so relativeTo.viewNames is exact geometry.
 *
 * Usage:
 *   node utils/render-orchestration-diagram.mjs <document.json> [orchestration name] [options]
 *
 * Options:
 *   --out <path>   Write the SVG to a path (single orchestration only).
 *   --outdir <dir> Directory for --all output. Default utils/out.
 *   --all          Render every orchestration in the document.
 *   --quiet        Suppress resolution warnings.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { esc, trunc, nameMaxChars, descMaxChars, slug } from './diagram-text.mjs';

const HERE = path.dirname(fileURLToPath(import.meta.url));

// ---------------------------------------------------------------------------
// Layout constants
// ---------------------------------------------------------------------------

const PAD = 20;
const CELL_W = 132;
const CELL_W_NARROW = 90;
const CELL_H = 34;
const PHASE_PAD = 10;
const PHASE_HEADER_H = 26;
const GUTTER = 22;
const BAND_GAP = 16;
const TRACK_H = 30;
const TRACK_GAP = 8;
const NEST_H = 38;
const NEST_GAP = 6;
const NARRATIVE_H = 20;
const NARRATIVE_GAP = 4;
const RAIL_CARD_W = 210;
const RAIL_CARD_H = 46;
const RAIL_GAP = 10;
// The band's heading is a line of text inside the band, so it needs its own height rather than
// sharing the gap above the cards — otherwise it sits on the band's own top edge.
const RAIL_LABEL_H = 22;
const FOOTNOTE_LINE_H = 15;
const MAX_WIDTH = 1600;
const MANY_VIEWS = 8;
const TOO_MANY_VIEWS = 12;

const COLOUR = {
  canvas: '#fafafa',
  card: '#ffffff',
  rule: '#d2d2d2',
  ruleFaint: '#e0e0e0',
  ink: '#151515',
  muted: '#6a6e73',
  spine: '#0066cc',
  spineWash: 'rgba(0,102,204,0.08)',
  narrativeWash: 'rgba(0,102,204,0.06)',
  nestFill: '#f8f8f8',
  edge: 'rgba(102,102,102,0.8)',
  entry: '#4ade80',
  exit: '#38bdf8',
  demand: '#facc15'
};

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

/**
 * Anchor for a pattern's landing page, following the convention in src/shared/AnchorUtils.html
 * (which today covers alphas and citations only, and gains patternAnchor on implementation).
 */
export function patternAnchor(patternName) {
  return 'pattern-' + slug(patternName);
}

/** Anchor for an orchestration's own landing page, for a stage that embeds one. */
export function orchestrationAnchor(orchestrationName) {
  return 'orchestration-' + slug(orchestrationName);
}

/**
 * A stage places either a pattern or a whole sub-orchestration. These read the target without
 * caring which, so the layout below is written once rather than branched at every use.
 */
export function stageTargetName(stage) {
  return (stage && (stage.orchestrationName || stage.patternName)) || '';
}

export function stageTargetKind(stage) {
  return stage && stage.orchestrationName ? 'orchestration' : 'pattern';
}

export function stageHostName(stage) {
  const host = stage && stage.relativeTo;
  if (!host) return '';
  return host.orchestrationName || host.patternName || '';
}

/**
 * Every region of the diagram navigates to one pattern — the block, its view cells, a nested
 * box, a track bar, a rail card. Pattern views are not separate targets: navSelectElement()
 * resolves a view only when its pattern is already the primary selection, and the agreed
 * behaviour is that a click lands on the pattern's own page.
 */
function link(href, inner) {
  if (!href) return inner;
  return `<a href="${esc(href)}" style="cursor: pointer;">${inner}</a>`;
}

// ---------------------------------------------------------------------------
// Layout
// ---------------------------------------------------------------------------

export function computeOrchestrationLayout(doc, orchestrationName) {
  const warnings = [];
  const orchestrations = doc.patternOrchestrations || [];
  const orch = orchestrationName
    ? orchestrations.find((o) => o.name === orchestrationName)
    : orchestrations[0];
  if (!orch) throw new Error(`No orchestration named "${orchestrationName}" in document`);

  const patternByName = new Map((doc.patterns || []).map((p) => [p.name, p]));
  const narrativeType = (doc.narrativeTypes || []).find((n) => n.name === orch.narrativeTypeName);
  if (orch.narrativeTypeName && !narrativeType) {
    warnings.push(`Orchestration declares narrativeTypeName "${orch.narrativeTypeName}" but no such NarrativeType is in scope`);
  }

  const orchByName = new Map(orchestrations.map((o) => [o.name, o]));

  const stages = (orch.stages || []).filter((s) => {
    if (stageTargetKind(s) === 'orchestration') {
      if (orchByName.has(s.orchestrationName)) return true;
      warnings.push(`Stage embeds orchestration "${s.orchestrationName}", which is not in scope — stage dropped`);
      return false;
    }
    if (patternByName.has(s.patternName)) return true;
    warnings.push(`Stage names pattern "${s.patternName}", which is not in scope — stage dropped`);
    return false;
  });

  // An embedded sub-endeavour draws as a single collapsed block. Its stages belong to its own
  // owner and its own diagram, so expanding them here would copy an ordering this orchestration
  // does not own -- the same reason the language has embedding rather than flattening.
  const views = (stage) => {
    if (stageTargetKind(stage) === 'orchestration') return [];
    const p = patternByName.get(stage.patternName);
    return [...(p.patternViews || [])].sort((a, b) => (a.seq || 0) - (b.seq || 0));
  };
  const targetLoops = (stage) => {
    if (stageTargetKind(stage) === 'orchestration') return false;
    return (patternByName.get(stage.patternName).patternViews || []).some((v) => v.loopsBackTo);
  };
  const targetDescription = (stage) => {
    const t = stageTargetKind(stage) === 'orchestration'
      ? orchByName.get(stage.orchestrationName)
      : patternByName.get(stage.patternName);
    return (t && t.description) || '';
  };
  const embeddedStageCount = (stage) =>
    ((orchByName.get(stage.orchestrationName) || {}).stages || []).length;

  // --- criteria numbering, in reading order -------------------------------
  const footnotes = [];
  const noteFor = (criterion, kind, stageLabel) => {
    if (!criterion) return null;
    const n = footnotes.length + 1;
    // A Background carries no name, so entry criteria fall back to their description as the
    // body and take no label of their own rather than repeating the kind twice.
    const text = (criterion.then || [])[0] || criterion.description || '';
    footnotes.push({ num: n, kind, stageLabel, label: criterion.name || null, text });
    return n;
  };

  // --- the sequential spine ------------------------------------------------
  const sequential = stages
    .filter((s) => s.relationship === 'sequential')
    .sort((a, b) => (a.seq || 0) - (b.seq || 0));

  const nestedByHost = new Map();
  const concurrentStages = stages.filter((s) => s.relationship === 'concurrent');
  const nestedStages = stages.filter((s) => s.relationship === 'nested');
  const demandStages = stages.filter((s) => s.relationship === 'onDemand');

  // How many nested rows each sequential host carries, so every block is the same height.
  for (const s of nestedStages) {
    const host = resolveHost(s, stages, warnings);
    if (!host) continue;
    nestedByHost.set(host, (nestedByHost.get(host) || 0) + 1);
  }
  const maxNestRows = Math.max(0, ...nestedByHost.values());

  const phaseH =
    PHASE_PAD + PHASE_HEADER_H + CELL_H +
    (maxNestRows > 0 ? maxNestRows * (NEST_H + NEST_GAP) : 0) +
    PHASE_PAD;

  // --- vertical cursor -----------------------------------------------------
  let y = PAD;
  const titleY = y + 17;
  const descY = titleY + 15;
  y = descY + 14;

  // --- phase blocks and their view cells -----------------------------------
  const viewX = new Map(); // patternName -> Map(viewName -> {x, w})
  const phases = [];
  let x = PAD;
  const narrativeBandTop = y; // filled in after we know how many rows it needs

  for (const stage of sequential) {
    const embedded = stageTargetKind(stage) === 'orchestration';
    const label = stageTargetName(stage);
    const vs = views(stage);
    const collapsed = vs.length > TOO_MANY_VIEWS;
    const cellW = collapsed || embedded ? CELL_W : vs.length > MANY_VIEWS ? CELL_W_NARROW : CELL_W;
    const cellCount = collapsed || embedded ? 1 : Math.max(1, vs.length);
    const w = cellCount * cellW + 2 * PHASE_PAD;

    const cellMap = new Map();
    const cells = [];
    const cellY = 0; // relative; absolute y set once the narrative band height is known
    if (embedded) {
      const n = embeddedStageCount(stage);
      cells.push({
        name: n === 1 ? '1 stage' : `${n} stages`,
        x: x + PHASE_PAD, w: cellW, collapsed: true, embedded: true
      });
    } else if (collapsed) {
      cells.push({ name: `${vs.length} phases`, x: x + PHASE_PAD, w: cellW, collapsed: true });
    } else if (vs.length === 0) {
      cells.push({ name: '', x: x + PHASE_PAD, w: cellW, collapsed: false });
    } else {
      vs.forEach((v, i) => {
        const cx = x + PHASE_PAD + i * cellW;
        cells.push({ name: v.name, x: cx, w: cellW, collapsed: false });
        cellMap.set(v.name, { x: cx, w: cellW });
      });
    }
    viewX.set(label, cellMap);

    phases.push({
      stage,
      patternName: label,
      embedded,
      description: targetDescription(stage),
      x,
      w,
      cells,
      cellY,
      loops: targetLoops(stage),
      entryNote: noteFor(stage.entryCriteria, 'entry', label),
      exitNote: noteFor(stage.exitCriteria, 'exit', label)
    });
    x += w + GUTTER;
  }
  const spineRight = phases.length ? phases[phases.length - 1].x + phases[phases.length - 1].w : PAD;

  // --- narrative strips, packed into rows ----------------------------------
  const narrativeRows = [];
  if (narrativeType && phases.length) {
    const elements = [...(narrativeType.narrativeElements || [])].sort((a, b) => (a.seq || 0) - (b.seq || 0));
    for (const el of elements) {
      const hit = phases.filter((p) =>
        (p.stage.narrativeContexts || []).some((nc) => nc.narrativeElementName === el.name)
      );
      if (!hit.length) continue;
      const left = Math.min(...hit.map((p) => p.x));
      const right = Math.max(...hit.map((p) => p.x + p.w));
      const strip = { label: el.name, x: left, w: right - left };
      let row = narrativeRows.find((r) => r.every((s) => s.x + s.w <= strip.x || strip.x + strip.w <= s.x));
      if (!row) { row = []; narrativeRows.push(row); }
      row.push(strip);
    }
  }
  const narrativeH = narrativeRows.length
    ? narrativeRows.length * NARRATIVE_H + (narrativeRows.length - 1) * NARRATIVE_GAP + BAND_GAP
    : 0;

  // Now that the narrative band height is known, pin the absolute y of everything below it.
  const spineY = narrativeBandTop + narrativeH;
  const narrativeStrips = [];
  narrativeRows.forEach((row, ri) => {
    row.forEach((s) => {
      narrativeStrips.push({ ...s, y: narrativeBandTop + ri * (NARRATIVE_H + NARRATIVE_GAP), h: NARRATIVE_H });
    });
  });

  for (const p of phases) {
    p.y = spineY;
    p.h = phaseH;
    p.headerY = spineY + PHASE_PAD;
    p.cellY = spineY + PHASE_PAD + PHASE_HEADER_H;
    p.cells.forEach((c) => { c.y = p.cellY; c.h = CELL_H; });
  }

  const connectors = [];
  for (let i = 0; i < phases.length - 1; i++) {
    const a = phases[i];
    const b = phases[i + 1];
    connectors.push({ x1: a.x + a.w, y1: a.y + a.h / 2, x2: b.x - 4, y2: b.y + b.h / 2 });
  }

  // --- span resolution against the column model ----------------------------
  function spanFor(stage) {
    const hostName = resolveHost(stage, stages, warnings);
    if (!hostName) {
      warnings.push(`Stage "${stageTargetName(stage)}" is placed relative to "${stageHostName(stage)}", which is not placed in this orchestration — parked as unanchored`);
      return null;
    }
    const hostPhase = phases.find((p) => p.patternName === hostName);
    if (!hostPhase) {
      warnings.push(`Stage "${stageTargetName(stage)}" resolves to host "${hostName}", which has no sequential placement — parked as unanchored`);
      return null;
    }
    const cellMap = viewX.get(hostName) || new Map();
    const wanted = (stage.relativeTo && stage.relativeTo.viewNames) || null;
    if (!wanted || !wanted.length) {
      const all = [...cellMap.values()];
      if (!all.length) return { hostPhase, cells: [], x: hostPhase.x + PHASE_PAD, w: hostPhase.w - 2 * PHASE_PAD };
      return { hostPhase, cells: [...cellMap.entries()].map(([name, c]) => ({ name, ...c })), x: Math.min(...all.map((c) => c.x)), w: Math.max(...all.map((c) => c.x + c.w)) - Math.min(...all.map((c) => c.x)) };
    }
    const found = [];
    for (const vn of wanted) {
      const c = cellMap.get(vn);
      if (!c) {
        warnings.push(`Stage "${stageTargetName(stage)}" scopes to view "${vn}" of "${hostName}", which has no such view — that view is ignored`);
        continue;
      }
      found.push({ name: vn, ...c });
    }
    if (!found.length) {
      warnings.push(`Stage "${stageTargetName(stage)}" scopes to no resolvable view of "${hostName}" — spanning the whole host`);
      const all = [...cellMap.values()];
      return { hostPhase, cells: [...cellMap.entries()].map(([name, c]) => ({ name, ...c })), x: Math.min(...all.map((c) => c.x)), w: Math.max(...all.map((c) => c.x + c.w)) - Math.min(...all.map((c) => c.x)) };
    }
    const left = Math.min(...found.map((c) => c.x));
    const right = Math.max(...found.map((c) => c.x + c.w));
    return { hostPhase, cells: found, x: left, w: right - left };
  }

  // --- nested stages, drawn inside their host ------------------------------
  const nested = [];
  const rowCursor = new Map();
  const unanchoredStages = [];
  for (const stage of nestedStages) {
    const span = spanFor(stage);
    // A nested stage with no resolvable host cannot be drawn inside anything, so it is parked
    // in the track band as a dashed bar rather than dropped from the diagram.
    if (!span) { unanchoredStages.push(stage); continue; }
    const note = noteFor(stage.exitCriteria, 'exit', stageTargetName(stage));
    const host = span.hostPhase;
    const row = rowCursor.get(host.patternName) || 0;
    rowCursor.set(host.patternName, row + 1);
    const by = host.cellY + CELL_H + NEST_GAP + row * (NEST_H + NEST_GAP);

    const boxes = [];
    if (stage.recurrence === 'perView' && span.cells.length) {
      span.cells.forEach((c) => boxes.push({ x: c.x + 2, y: by, w: c.w - 4, h: NEST_H }));
    } else {
      boxes.push({ x: span.x + 2, y: by, w: span.w - 4, h: NEST_H });
    }
    nested.push({
      stage,
      patternName: stageTargetName(stage),
      embedded: stageTargetKind(stage) === 'orchestration',
      hostName: host.patternName,
      recurrence: stage.recurrence || 'once',
      loops: targetLoops(stage),
      viewCount: views(stage).length,
      boxes,
      exitNote: note
    });
  }

  // --- concurrent tracks ---------------------------------------------------
  const concurrent = [];
  const trackBandTop = spineY + phaseH + BAND_GAP;
  const sortedConcurrent = concurrentStages
    .map((stage) => ({ stage, span: spanFor(stage) }))
    .concat(unanchoredStages.map((stage) => ({ stage, span: null })))
    .sort((a, b) => {
      const ax = a.span ? a.span.x : Infinity;
      const bx = b.span ? b.span.x : Infinity;
      if (ax !== bx) return ax - bx;
      return (b.span ? b.span.w : 0) - (a.span ? a.span.w : 0);
    });
  // The first track of each host reaches up to it. Keying this on the host rather than on the
  // row means a second host further along the spine still gets a leader, instead of every track
  // below the very first one dangling. Later tracks of a host take a short tick, because their
  // leader would be drawn through the bars already sitting between them and the block.
  const hostsWithLeader = new Set();
  // Two tracks only collide if their spans overlap horizontally, so they pack into shared rows
  // by first fit — the same rule the narrative strips above use. A single descending cursor
  // would push a later host's tracks below the earlier host's, stranding them well under the
  // block they run alongside even though the column beside it is empty.
  const trackRows = [];
  sortedConcurrent.forEach(({ stage, span }) => {
    const note = noteFor(stage.exitCriteria, 'exit', stageTargetName(stage));
    const unanchored = !span;
    const hostKey = span ? span.hostPhase.patternName : null;
    const firstForHost = hostKey !== null && !hostsWithLeader.has(hostKey);
    if (firstForHost) hostsWithLeader.add(hostKey);
    const bx = unanchored ? PAD : span.x;
    const bw = unanchored ? spineRight - PAD : span.w;
    let rowIndex = trackRows.findIndex((r) => r.every((b) => b.x + b.w <= bx || bx + bw <= b.x));
    if (rowIndex === -1) { trackRows.push([]); rowIndex = trackRows.length - 1; }
    trackRows[rowIndex].push({ x: bx, w: bw });
    const trackY = trackBandTop + rowIndex * (TRACK_H + TRACK_GAP);
    concurrent.push({
      stage,
      patternName: stageTargetName(stage),
      embedded: stageTargetKind(stage) === 'orchestration',
      unanchored,
      loops: targetLoops(stage),
      viewCount: views(stage).length,
      scopedTo: span && span.cells.length && stage.relativeTo && stage.relativeTo.viewNames ? span.cells.map((c) => c.name) : null,
      hostName: span ? span.hostPhase.patternName : null,
      x: bx,
      y: trackY,
      w: bw,
      h: TRACK_H,
      leaderTop: firstForHost ? span.hostPhase.y + span.hostPhase.h : trackY - 8,
      exitNote: note
    });
  });
  let cursor = trackRows.length
    ? trackBandTop + trackRows.length * (TRACK_H + TRACK_GAP) - TRACK_GAP + BAND_GAP
    : spineY + phaseH + BAND_GAP;

  // --- the on-demand rail --------------------------------------------------
  let rail = null;
  if (demandStages.length) {
    const availableW = Math.max(spineRight - PAD, RAIL_CARD_W + 2 * RAIL_GAP);
    const perRow = Math.max(1, Math.floor((availableW - RAIL_GAP) / (RAIL_CARD_W + RAIL_GAP)));
    const rows = Math.ceil(demandStages.length / perRow);
    const railH = RAIL_LABEL_H + RAIL_GAP + rows * RAIL_CARD_H + (rows - 1) * RAIL_GAP + RAIL_GAP;
    const cards = demandStages.map((stage, i) => {
      const r = Math.floor(i / perRow);
      const c = i % perRow;
      const t = stage.trigger || {};
      return {
        stage,
        patternName: stageTargetName(stage),
        embedded: stageTargetKind(stage) === 'orchestration',
        trigger: (t.when || [])[0] || t.description || '',
        note: noteFor(stage.trigger, 'trigger', stageTargetName(stage)),
        x: PAD + RAIL_GAP + c * (RAIL_CARD_W + RAIL_GAP),
        y: cursor + RAIL_LABEL_H + RAIL_GAP + r * (RAIL_CARD_H + RAIL_GAP),
        w: RAIL_CARD_W,
        h: RAIL_CARD_H
      };
    });
    rail = { x: PAD, y: cursor, w: availableW, h: railH, cards };
    cursor += railH + BAND_GAP;
  }

  // --- footnotes and legend ------------------------------------------------
  const footnoteBand = footnotes.length
    ? { x: PAD, y: cursor, h: 16 + footnotes.length * FOOTNOTE_LINE_H }
    : null;
  if (footnoteBand) cursor += footnoteBand.h + BAND_GAP;

  const legend = { x: PAD, y: cursor, h: 34 };
  cursor += legend.h;

  const width = Math.max(spineRight, rail ? rail.x + rail.w : 0, 640) + PAD;
  const height = cursor + PAD;
  // Width is reported, not constrained. A layered timeline cannot wrap, and an endeavour with
  // many phases is legitimately wide, so the container scrolls horizontally rather than the
  // diagram being shrunk or split.
  const overViewport = width > MAX_WIDTH;

  return {
    name: orch.name,
    description: orch.description || '',
    narrativeTypeName: orch.narrativeTypeName || null,
    width,
    height,
    overViewport,
    titleY,
    descY,
    narrativeStrips,
    phases,
    connectors,
    nested,
    concurrent,
    rail,
    footnotes,
    footnoteBand,
    legend,
    warnings
  };
}

/** Walk relativeTo until it lands on a sequential stage. Returns a pattern name or null. */
function resolveHost(stage, stages, warnings) {
  let name = stageHostName(stage);
  const seen = new Set();
  for (let depth = 0; depth < 5 && name; depth++) {
    if (seen.has(name)) {
      warnings.push(`Stage "${stageTargetName(stage)}" has a cyclical relativeTo chain through "${name}"`);
      return null;
    }
    seen.add(name);
    const hostStage = stages.find((s) => stageTargetName(s) === name && s.relationship === 'sequential');
    if (hostStage) return name;
    const indirect = stages.find((s) => stageTargetName(s) === name);
    if (!indirect || !indirect.relativeTo) return null;
    name = stageHostName(indirect);
  }
  return null;
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

function noteGlyph(cx, cy, num, colour) {
  return (
    `<circle cx="${cx}" cy="${cy}" r="7" fill="${COLOUR.card}" stroke="${colour}" stroke-width="1.5"/>` +
    textEl(cx, cy + 3, String(num), { size: 8, weight: 600, fill: COLOUR.muted, anchor: 'middle' })
  );
}

export function renderStaticSvg(layout, opts = {}) {
  // Supply href: () => null to render a diagram with no links at all.
  const href = opts.href === undefined
    ? (name, kindOrEmbedded) =>
        '#' + (kindOrEmbedded ? orchestrationAnchor(name) : patternAnchor(name))
    : opts.href;
  const out = [];
  out.push(`<svg xmlns="http://www.w3.org/2000/svg" width="${layout.width}" height="${layout.height}" viewBox="0 0 ${layout.width} ${layout.height}">`);
  out.push(
    `<defs><marker id="orch-arrow" markerWidth="7" markerHeight="5" refX="7" refY="2.5" orient="auto">` +
    `<polygon points="0 0, 7 2.5, 0 5" fill="${COLOUR.edge}"/></marker></defs>`
  );
  out.push(`<rect width="${layout.width}" height="${layout.height}" fill="${COLOUR.canvas}" rx="4"/>`);

  // Title
  out.push(textEl(PAD, layout.titleY, layout.name, { size: 16, weight: 700 }));
  if (layout.description) {
    out.push(textEl(PAD, layout.descY, trunc(layout.description, descMaxChars(layout.width - 2 * PAD)), { size: 10, fill: COLOUR.muted }));
  }

  // Narrative band
  for (const s of layout.narrativeStrips) {
    out.push(`<rect x="${s.x}" y="${s.y}" width="${s.w}" height="${s.h}" rx="3" fill="${COLOUR.narrativeWash}" stroke="${COLOUR.ruleFaint}" stroke-width="0.5"/>`);
    out.push(textEl(s.x + 8, s.y + 14, s.label.toUpperCase(), { size: 9, weight: 600, fill: COLOUR.muted, letterSpacing: '0.08em' }));
  }
  if (layout.narrativeTypeName && layout.narrativeStrips.length) {
    const last = layout.narrativeStrips[layout.narrativeStrips.length - 1];
    out.push(textEl(layout.width - PAD, last.y + last.h + 0, `narrative: ${layout.narrativeTypeName}`, { size: 9, fill: COLOUR.muted, anchor: 'end' }));
  }

  // Connectors, under the blocks
  for (const c of layout.connectors) {
    out.push(`<line x1="${c.x1}" y1="${c.y1}" x2="${c.x2}" y2="${c.y2}" stroke="${COLOUR.edge}" stroke-width="1.5" marker-end="url(#orch-arrow)"/>`);
  }

  // Concurrent leaders, drawn before the bars so the bars sit on top
  for (const t of layout.concurrent) {
    if (t.unanchored) continue;
    for (const lx of [t.x, t.x + t.w]) {
      out.push(`<line x1="${lx}" y1="${t.leaderTop}" x2="${lx}" y2="${t.y}" stroke="${COLOUR.rule}" stroke-width="1" stroke-dasharray="2 3"/>`);
    }
  }

  // Phase blocks
  for (const p of layout.phases) {
    const headerW = p.w - 2 * PHASE_PAD;
    const block = [];
    // An embedded sub-endeavour is drawn dashed and flagged, because it is a reference to an
    // endeavour with its own owner and its own diagram rather than work detailed here.
    const embedDash = p.embedded ? ` stroke-dasharray="6 3"` : '';
    block.push(`<rect x="${p.x}" y="${p.y}" width="${p.w}" height="${p.h}" rx="4" fill="${COLOUR.card}" stroke="${COLOUR.spine}" stroke-width="1.5"${embedDash}/>`);
    block.push(textEl(p.x + PHASE_PAD, p.y + PHASE_PAD + 13, trunc(p.patternName, nameMaxChars(headerW - 14)), { size: 11, weight: 600 }));
    if (p.embedded) block.push(textEl(p.x + p.w - PHASE_PAD, p.y + PHASE_PAD + 13, '↗', { size: 12, fill: COLOUR.muted, anchor: 'end' }));
    else if (p.loops) block.push(textEl(p.x + p.w - PHASE_PAD, p.y + PHASE_PAD + 13, '↻', { size: 12, fill: COLOUR.muted, anchor: 'end' }));
    block.push(textEl(p.x + PHASE_PAD, p.y + PHASE_PAD + 24, trunc(p.description, descMaxChars(headerW)), { size: 8, fill: COLOUR.muted }));

    for (const c of p.cells) {
      block.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" fill="${COLOUR.card}" stroke="${COLOUR.rule}" stroke-width="0.5"/>`);
      block.push(textEl(c.x + 8, c.y + 21, trunc(c.name, nameMaxChars(c.w - 16)), { size: 10, fill: c.collapsed ? COLOUR.muted : COLOUR.ink }));
    }
    out.push(link(href(p.patternName, p.embedded), block.join('\n')));

    if (p.entryNote) {
      out.push(`<rect x="${p.x - 3}" y="${p.y + 8}" width="6" height="${p.h - 16}" rx="3" fill="${COLOUR.entry}"/>`);
      out.push(noteGlyph(p.x, p.y - 9, p.entryNote, COLOUR.entry));
    }
    if (p.exitNote) {
      out.push(`<rect x="${p.x + p.w - 3}" y="${p.y + 8}" width="6" height="${p.h - 16}" rx="3" fill="${COLOUR.exit}"/>`);
      out.push(noteGlyph(p.x + p.w, p.y - 9, p.exitNote, COLOUR.exit));
    }
  }

  // Nested stages, inside their host
  for (const n of layout.nested) {
    if (n.unanchored) continue;
    n.boxes.forEach((b, i) => {
      const box = [];
      box.push(`<rect x="${b.x}" y="${b.y}" width="${b.w}" height="${b.h}" rx="4" fill="${COLOUR.nestFill}" stroke="${COLOUR.muted}" stroke-width="1" stroke-dasharray="4 3"/>`);
      const label = trunc(n.patternName, nameMaxChars(b.w - 26));
      box.push(textEl(b.x + 8, b.y + 16, label, { size: 10, weight: 600 }));
      if (n.embedded) box.push(textEl(b.x + b.w - 8, b.y + 16, '↗', { size: 11, fill: COLOUR.muted, anchor: 'end' }));
      else if (n.loops) box.push(textEl(b.x + b.w - 8, b.y + 16, '↻', { size: 11, fill: COLOUR.muted, anchor: 'end' }));
      const unit = n.embedded ? 'endeavour' : `${n.viewCount} phases`;
      const sub = n.recurrence === 'perView' ? `repeats · ${unit}` : unit;
      box.push(textEl(b.x + 8, b.y + 29, trunc(sub, descMaxChars(b.w - 16)), { size: 8, fill: COLOUR.muted }));
      out.push(link(href(n.patternName, n.embedded), box.join('\n')));
      if (n.exitNote && i === n.boxes.length - 1) {
        out.push(noteGlyph(b.x + b.w - 8, b.y + b.h - 2, n.exitNote, COLOUR.exit));
      }
    });
  }

  // Concurrent tracks
  for (const t of layout.concurrent) {
    const dash = t.unanchored ? ` stroke-dasharray="5 4"` : t.embedded ? ` stroke-dasharray="6 3"` : '';
    const bar = [];
    bar.push(`<rect x="${t.x}" y="${t.y}" width="${t.w}" height="${t.h}" rx="${t.h / 2}" fill="${COLOUR.spineWash}" stroke="${t.unanchored ? COLOUR.muted : COLOUR.spine}" stroke-width="1"${dash}/>`);
    bar.push(textEl(t.x + 14, t.y + 14, trunc(t.patternName, nameMaxChars(t.w - 40)), { size: 10, weight: 600 }));
    if (t.embedded) bar.push(textEl(t.x + t.w - 14, t.y + 14, '↗', { size: 11, fill: COLOUR.muted, anchor: 'end' }));
    const scope = t.unanchored
      ? 'unanchored — host not placed'
      : t.scopedTo
        ? `alongside ${t.hostName} · ${t.scopedTo.join(', ')}`
        : `alongside ${t.hostName}`;
    bar.push(textEl(t.x + 14, t.y + 25, trunc(scope, descMaxChars(t.w - 28)), { size: 8, fill: COLOUR.muted }));
    out.push(link(href(t.patternName, t.embedded), bar.join('\n')));
    if (t.exitNote) out.push(noteGlyph(t.x + t.w, t.y + t.h / 2, t.exitNote, COLOUR.exit));
  }

  // On-demand rail
  if (layout.rail) {
    const r = layout.rail;
    out.push(`<rect x="${r.x}" y="${r.y}" width="${r.w}" height="${r.h}" rx="4" fill="none" stroke="${COLOUR.rule}" stroke-width="1" stroke-dasharray="6 4"/>`);
    out.push(textEl(r.x + RAIL_GAP, r.y + 15, 'REACHED FOR ON DEMAND', { size: 9, weight: 600, fill: COLOUR.muted, letterSpacing: '0.08em' }));
    out.push(textEl(r.x + r.w - RAIL_GAP, r.y + 15, 'no fixed position — entered when the trigger is recognised', { size: 8, fill: COLOUR.muted, anchor: 'end' }));
    for (const c of r.cards) {
      const card = [];
      card.push(`<rect x="${c.x}" y="${c.y}" width="${c.w}" height="${c.h}" rx="4" fill="${COLOUR.card}" stroke="${COLOUR.rule}" stroke-width="1"/>`);
      card.push(`<rect x="${c.x}" y="${c.y + 1}" width="3" height="${c.h - 2}" rx="1.5" fill="${COLOUR.demand}"/>`);
      card.push(textEl(c.x + 12, c.y + 18, trunc(c.patternName, nameMaxChars(c.w - 34)), { size: 10, weight: 600 }));
      card.push(textEl(c.x + 12, c.y + 33, trunc(`when ${c.trigger}`, descMaxChars(c.w - 34)), { size: 8, fill: COLOUR.muted }));
      out.push(link(href(c.patternName, c.embedded), card.join('\n')));
      if (c.note) out.push(noteGlyph(c.x + c.w - 2, c.y + c.h - 2, c.note, COLOUR.demand));
    }
  }

  // Footnotes
  if (layout.footnoteBand) {
    const f = layout.footnoteBand;
    out.push(textEl(f.x, f.y + 10, 'CRITERIA', { size: 9, weight: 600, fill: COLOUR.muted, letterSpacing: '0.08em' }));
    layout.footnotes.forEach((n, i) => {
      const ly = f.y + 16 + i * FOOTNOTE_LINE_H + 9;
      const colour = n.kind === 'entry' ? COLOUR.entry : n.kind === 'trigger' ? COLOUR.demand : COLOUR.exit;
      out.push(noteGlyph(f.x + 7, ly - 3, n.num, colour));
      const kindLabel = n.kind === 'entry' ? 'Entry' : n.kind === 'trigger' ? 'Trigger' : 'Exit';
      const head = n.label
        ? `${n.stageLabel} · ${kindLabel} — ${n.label}`
        : `${n.stageLabel} · ${kindLabel}`;
      // One text element with tspans, so the body flows from the end of the bold head rather
      // than being positioned by a character-width guess.
      out.push(
        `<text x="${f.x + 20}" y="${ly}" font-family="sans-serif" font-size="9" fill="${COLOUR.ink}" xml:space="preserve">` +
        `<tspan font-weight="600">${esc(head)}:</tspan>` +
        `<tspan fill="${COLOUR.muted}">  ${esc(trunc(n.text, descMaxChars(layout.width - f.x - 20 - PAD) - head.length))}</tspan>` +
        `</text>`
      );
    });
  }

  // Legend
  const L = layout.legend;
  let lx = L.x;
  const ly = L.y + 10;
  const swatch = (draw, label, width) => {
    out.push(draw(lx, ly));
    out.push(textEl(lx + 34, ly + 11, label, { size: 9, fill: COLOUR.muted }));
    lx += 34 + 7 * label.length + 22;
  };
  // Only the relationships the orchestration actually uses — a key to shapes that are not on
  // the page is noise.
  if (layout.phases.length) {
    swatch((sx, sy) => `<rect x="${sx}" y="${sy}" width="26" height="16" rx="3" fill="${COLOUR.card}" stroke="${COLOUR.spine}" stroke-width="1.5"/>`, 'Sequential phase');
  }
  if (layout.concurrent.length) {
    swatch((sx, sy) => `<rect x="${sx}" y="${sy}" width="26" height="16" rx="8" fill="${COLOUR.spineWash}" stroke="${COLOUR.spine}" stroke-width="1"/>`, 'Concurrent track');
  }
  if (layout.nested.length) {
    swatch((sx, sy) => `<rect x="${sx}" y="${sy}" width="26" height="16" rx="3" fill="${COLOUR.nestFill}" stroke="${COLOUR.muted}" stroke-width="1" stroke-dasharray="4 3"/>`, 'Nested  ↻ repeats');
  }
  if (layout.rail) {
    swatch((sx, sy) => `<rect x="${sx}" y="${sy}" width="26" height="16" rx="3" fill="${COLOUR.card}" stroke="${COLOUR.rule}" stroke-width="1"/><rect x="${sx}" y="${sy + 1}" width="3" height="14" rx="1.5" fill="${COLOUR.demand}"/>`, 'On demand');
  }

  out.push('</svg>');
  return out.join('\n');
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  if (argv.includes('--help')) {
    console.log('Usage: node render-orchestration-diagram.mjs <document.json> [orchestration name] [--all] [--out <path>] [--outdir <dir>] [--quiet]');
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
    throw new Error('Usage: node utils/render-orchestration-diagram.mjs <document.json> [orchestration name] [--all] [--out <path>] [--outdir <dir>]');
  }
  opts.document = positional[0];
  opts.orchestration = positional[1] || null;
  return opts;
}

function main() {
  const opts = parseArgs(process.argv.slice(2));
  const doc = JSON.parse(fs.readFileSync(opts.document, 'utf8'));
  const all = doc.patternOrchestrations || [];
  if (!all.length) throw new Error('Document declares no patternOrchestrations');

  const targets = opts.all ? all.map((o) => o.name) : [opts.orchestration || all[0].name];
  let warned = 0;

  for (const name of targets) {
    const layout = computeOrchestrationLayout(doc, name);
    const svg = renderStaticSvg(layout);
    const outPath = opts.out && targets.length === 1
      ? opts.out
      : path.join(opts.outdir, `${slug(name)}.svg`);
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    fs.writeFileSync(outPath, svg + '\n');
    const scrolls = layout.overViewport ? ' (wider than a typical viewport — container scrolls)' : '';
    console.log(`${name}: ${layout.width}×${layout.height}${scrolls} → ${outPath}`);
    if (!opts.quiet) {
      for (const w of layout.warnings) {
        warned++;
        console.error(`  warning: ${w}`);
      }
    }
  }
  if (warned) process.exitCode = 0; // warnings report, they do not fail the render
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(fileURLToPath(import.meta.url))) {
  main();
}
