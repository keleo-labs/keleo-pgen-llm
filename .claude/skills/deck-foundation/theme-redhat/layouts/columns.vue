<!--
  Two to four parallel points, each opened by the template's red rule.

  Content comes from frontmatter rather than slots because the items are
  structurally identical: expressing them as data keeps the markdown short
  and makes the count explicit, which is what governs the grid.

  ---
  layout: columns
  items:
    - heading: Golden paths
      body: Defaults that are faster than the workaround.
    - heading: Self-service
      body: No ticket between intent and environment.
  ---
  # Three forces decide whether a platform scales
-->
<script setup lang="ts">
interface Column {
  heading: string
  body?: string
}

interface Source {
  label: string
  url?: string
}

const props = defineProps<{
  items: Column[]
  sources?: Source[]
}>()

// The template's rule weights step from full red to pale across a row, which
// reads as one group rather than a set of unrelated boxes. The ramp must
// descend monotonically — returning to a darker tint on the fourth column
// reads as an error rather than a system.
const rules = ['rh-rule', 'rh-rule-light', 'rh-rule-pale', 'rh-rule-pale']

const count = Math.min(Math.max(props.items?.length ?? 0, 1), 4)
</script>

<template>
  <div class="slidev-layout rh-columns">
    <div class="rh-columns__head">
      <slot />
    </div>
    <div class="rh-columns__grid" :style="{ gridTemplateColumns: `repeat(${count}, 1fr)` }">
      <div
        v-for="(item, i) in items"
        :key="i"
        class="rh-columns__item"
        :class="rules[i % rules.length]"
      >
        <div class="rh-columns__heading">{{ item.heading }}</div>
        <div v-if="item.body" class="rh-columns__body">{{ item.body }}</div>
      </div>
    </div>
    <SourceNote :sources="sources" />
  </div>
</template>

<style scoped>
.rh-columns {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Reserved two-line title zone — see the note in default.vue. */
.rh-columns__head :deep(h1) {
  font-family: var(--rh-font-display);
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.01em;
  min-height: 2.3em;
  margin: 0 0 1.5rem 0;
  max-width: 22ch;
}

/* Columns centre in the space under the title rather than hugging it, so
   short entries do not leave the foot of the slide empty.

   The two content rows are declared on the outer grid and each column opts
   into them with subgrid, so a heading that wraps to two lines does not
   push its own body out of line with its neighbours'. Without this the
   bodies start at different heights and the row stops reading as a set. */
.rh-columns__grid {
  display: grid;
  grid-template-rows: auto auto;
  column-gap: 2.25rem;
  row-gap: 0;
  flex: 1;
  align-content: center;
}

.rh-columns__item {
  display: grid;
  grid-row: span 2;
  grid-template-rows: subgrid;
}

.rh-columns__heading {
  font-family: var(--rh-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 1.1rem;
}

.rh-columns__body {
  font-size: 1.0625rem;
  line-height: 1.5;
  color: var(--rh-grey-text);
}
</style>
