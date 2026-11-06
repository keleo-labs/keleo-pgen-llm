import assert from 'node:assert/strict';
import { test } from 'node:test';
import { computePatternMatrixLayout, renderStaticSvg } from './render-pattern-matrix.mjs';

const doc = {
  focuses: [{ name: 'Value' }],
  alphas: [{ name: 'Plan', focusName: 'Value' }],
  patterns: [{
    name: 'Planning Lifecycle',
    patternViews: [
      { name: 'Discover', seq: 0, alphaStates: [{ alphaName: 'Plan', stateName: 'Researched' }] },
      { name: 'Approve', seq: 1, alphaStates: [{ alphaName: 'Plan', stateName: 'Approved' }] },
      { name: 'Renew', seq: 2, alphaStates: [{ alphaName: 'Plan', stateName: 'Renewed' }], loopsBackTo: {
        patternViewName: 'Discover', condition: { name: 'More planning agreed' }
      } }
    ]
  }]
};

test('a split pattern labels its part and retains a guarded return to the earlier part', () => {
  const excerpt = structuredClone(doc);
  excerpt.patterns[0].patternViews = excerpt.patterns[0].patternViews.slice(1);
  const layout = computePatternMatrixLayout(excerpt, 'Planning Lifecycle', {
    noteOffset: 1, externalLoopPart: 'Part 1'
  });
  const svg = renderStaticSvg(layout, { title: 'Planning Lifecycle — Part 2' });
  assert.equal(layout.loops.length, 1);
  assert.equal(layout.loops[0].fromName, 'Renew');
  assert.equal(layout.loops[0].toName, 'Discover');
  assert.ok(layout.loops[0].segments[1].x2 < layout.loops[0].segments[1].x1);
  assert.match(svg, /Planning Lifecycle — Part 2/);
  assert.match(svg, /More planning agreed.*Discover \(Part 1\)/);
});
