<!--
  A sequence: phases, stages, or a method. Mirrors the template's chevron and
  timeline layouts without drawing arrow shapes, which the pptx exporter
  would rasterise. Order is carried by numbering and the rule weight instead.

  ---
  layout: steps
  items:
    - heading: Establish
      body: One team, one golden path, measured.
    - heading: Extend
      body: Second and third teams onboard self-service.
  ---
  # Adoption succeeds in three deliberate stages
-->
<script setup lang="ts">
interface Step {
  heading: string
  body?: string
  caption?: string
}

interface Source {
  label: string
  url?: string
}

const props = withDefaults(
  defineProps<{
    items: Step[]
    numbered?: boolean
    sources?: Source[]
  }>(),
  { numbered: true },
)

// Descends monotonically — a fourth step lighter than the third would read
// as a mistake. See the same ramp in columns.vue.
const rules = ['rh-rule', 'rh-rule-light', 'rh-rule-pale', 'rh-rule-pale']
const count = Math.min(Math.max(props.items?.length ?? 0, 1), 4)
</script>

<template>
  <div class="slidev-layout rh-steps">
    <div class="rh-steps__head">
      <slot />
    </div>
    <div class="rh-steps__grid" :style="{ gridTemplateColumns: `repeat(${count}, 1fr)` }">
      <div
        v-for="(item, i) in items"
        :key="i"
        class="rh-steps__item"
        :class="rules[i % rules.length]"
      >
        <div v-if="numbered" class="rh-steps__index">{{ String(i + 1).padStart(2, '0') }}</div>
        <div class="rh-steps__heading">{{ item.heading }}</div>
        <div v-if="item.body" class="rh-steps__body">{{ item.body }}</div>
        <div v-if="item.caption" class="rh-steps__caption">{{ item.caption }}</div>
      </div>
    </div>
    <SourceNote :sources="sources" />
  </div>
</template>

<style scoped>
.rh-steps {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Reserved two-line title zone — see the note in default.vue. */
.rh-steps__head :deep(h1) {
  font-family: var(--rh-font-display);
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.01em;
  min-height: 2.3em;
  margin: 0 0 1.5rem 0;
  max-width: 22ch;
}

/* The grid takes the space under the title and centres within it. Hugging
   the title instead leaves a block of dead space at the foot of the slide
   whenever the columns are short.

   Four content rows are declared here and each step opts into them with
   subgrid, so a heading that wraps to two lines does not drag its own body
   and caption out of line with the neighbouring steps'. */
.rh-steps__grid {
  display: grid;
  grid-template-rows: auto auto auto auto;
  column-gap: 2rem;
  row-gap: 0;
  flex: 1;
  align-content: center;
}

.rh-steps__item {
  display: grid;
  grid-row: span 4;
  grid-template-rows: subgrid;
}

/* Rows are assigned explicitly rather than left to auto-placement: an item
   with a caption but no body would otherwise place its caption in the body
   row and sit out of line with the rest. */
.rh-steps__index { grid-row: 1; }
.rh-steps__heading { grid-row: 2; }
.rh-steps__body { grid-row: 3; }
.rh-steps__caption { grid-row: 4; }

.rh-steps__index {
  font-family: var(--rh-font-display);
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--rh-red);
  margin-bottom: 0.375rem;
}

.rh-steps__heading {
  font-family: var(--rh-font-display);
  font-size: 1.375rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 1.1rem;
}

.rh-steps__body {
  font-size: 1.0625rem;
  line-height: 1.5;
  color: var(--rh-grey-text);
}

/* Generous clearance, not decoration. The exporter sizes each text shape
   from the browser's measurement, but PowerPoint lays the same string out
   in a slightly taller line box — so a body sized exactly to its content
   overruns and lands on top of the caption. ~1.75rem absorbs the drift. */
.rh-steps__caption {
  margin-top: 1.75rem;
  font-size: 0.875rem;
  color: var(--rh-grey-text);
}
</style>
