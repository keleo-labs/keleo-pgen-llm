<!--
  One to three headline figures with their interpretation.

  A number without a reading is decoration, so `label` is required and the
  figure is sized to dominate. Keep `value` short — "62%", "3x", "£1.4m" —
  since the display face is set tight and long strings will wrap badly.

  ---
  layout: stats
  items:
    - value: "62%"
      label: of platform initiatives plateau after the pilot team
      source: Internal adoption review, 2026
  ---
  # Adoption flattens without an owning team
-->
<script setup lang="ts">
interface Stat {
  value: string
  label: string
  source?: string
}

interface Source {
  label: string
  url?: string
}

const props = defineProps<{
  items: Stat[]
  sources?: Source[]
}>()

const count = Math.min(Math.max(props.items?.length ?? 0, 1), 3)
const single = count === 1
</script>

<template>
  <div class="slidev-layout rh-stats">
    <div class="rh-stats__head">
      <slot />
    </div>
    <!-- A lone figure reads better beside its explanation than above it, so
         it gets its own markup rather than a grid override. -->
    <div v-if="single" class="rh-stats__solo">
      <div class="rh-stats__value rh-stats__value--single">{{ items[0].value }}</div>
      <div>
        <div class="rh-stats__label">{{ items[0].label }}</div>
        <div v-if="items[0].source" class="rh-stats__source">{{ items[0].source }}</div>
      </div>
    </div>
    <div
      v-else
      class="rh-stats__grid"
      :style="{ gridTemplateColumns: `repeat(${count}, 1fr)` }"
    >
      <div v-for="(item, i) in items" :key="i" class="rh-stats__item">
        <div class="rh-stats__value">{{ item.value }}</div>
        <div class="rh-stats__label">{{ item.label }}</div>
        <div v-if="item.source" class="rh-stats__source">{{ item.source }}</div>
      </div>
    </div>
    <SourceNote :sources="sources" />
  </div>
</template>

<style scoped>
.rh-stats {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Reserved two-line title zone — see the note in default.vue. */
.rh-stats__head :deep(h1) {
  font-family: var(--rh-font-display);
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.01em;
  min-height: 2.3em;
  margin: 0 0 1.5rem 0;
  max-width: 22ch;
}

/* Figures centre in the space under the title rather than hugging it, so a
   short row does not leave the foot of the slide empty.

   Each figure opts into the three shared rows with subgrid. A value that
   wraps — "July 2026" against "$5bn" — would otherwise push its own label
   and source down and break the row's horizontal reading line. */
.rh-stats__grid {
  display: grid;
  grid-template-rows: auto auto auto;
  column-gap: 2.5rem;
  row-gap: 0;
  flex: 1;
  align-content: center;
}

.rh-stats__item {
  display: grid;
  grid-row: span 3;
  grid-template-rows: subgrid;
}

.rh-stats__solo {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 3rem;
}

.rh-stats__value {
  font-family: var(--rh-font-display);
  font-size: 4rem;
  font-weight: 700;
  line-height: 1;
  color: var(--rh-red);
  margin-bottom: 1.25rem;
}

/* A solo figure is the whole slide, so it is sized to carry it. At the row
   size it read as a caption with a lot of white space around it. */
.rh-stats__value--single {
  font-size: 10rem;
  margin-bottom: 0;
}

.rh-stats__label {
  font-size: 1.1875rem;
  line-height: 1.45;
  max-width: 34ch;
}

.rh-stats__solo .rh-stats__label {
  font-size: 1.5rem;
  line-height: 1.4;
  max-width: 26ch;
}

/* See the note on .rh-steps__caption — PowerPoint's taller line boxes make
   a label overrun the shape the exporter measured for it, and the source
   line underneath is what it lands on. */
.rh-stats__source {
  margin-top: 1.75rem;
  font-size: 0.875rem;
  color: var(--rh-grey-text);
}

/* The solo label is set larger, so its line box drifts further than the row
   variant's and 1.75rem leaves the source visibly crowding it. */
.rh-stats__solo .rh-stats__source {
  margin-top: 2.25rem;
}
</style>
