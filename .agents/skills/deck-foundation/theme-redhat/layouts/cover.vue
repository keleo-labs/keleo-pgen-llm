<!--
  Opening slide. Dark by default because the template's cover treatments are
  high-contrast; set `variant: red` or `variant: light` to change it.

  Background colour is applied as a class on the root element, not via the
  frontmatter `background:` key — frontmatter backgrounds are dropped by the
  pptx export, while a class-applied fill converts to a real shape fill.

  The speaker is `byline`, not `presenter`: Slidev reserves `presenter` as a
  config key for presenter mode, so it never reaches the layout as a prop.
-->
<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: 'dark' | 'red' | 'light'
    eyebrow?: string
    byline?: string
    date?: string
  }>(),
  { variant: 'dark' },
)

const surface = {
  dark: 'rh-on-dark',
  red: 'rh-on-red',
  light: '',
}[props.variant]
</script>

<template>
  <div class="slidev-layout rh-cover" :class="surface">
    <div class="rh-cover__body">
      <div class="rh-cover__accent" />
      <div v-if="eyebrow" class="rh-eyebrow rh-cover__eyebrow">{{ eyebrow }}</div>
      <slot />
    </div>
    <div v-if="byline || date" class="rh-cover__meta">
      <span v-if="byline">{{ byline }}</span>
      <span v-if="byline && date"> · </span>
      <span v-if="date">{{ date }}</span>
    </div>
  </div>
</template>

<style scoped>
.rh-cover {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

.rh-cover__body :deep(h1) {
  font-family: var(--rh-font-display);
  font-size: 4.25rem;
  font-weight: 700;
  line-height: 1.05;
  letter-spacing: -0.02em;
  /* Wide enough that PowerPoint's taller line boxes cannot push the title's
     descenders into the subtitle — see DECK-FOUNDATION.md §4. At display
     size the drift is proportionally larger, so this gap is larger too. */
  margin: 0 0 2.75rem 0;
  max-width: 20ch;
}

.rh-cover__body :deep(p) {
  font-size: 1.5rem;
  line-height: 1.4;
  margin: 0;
  max-width: 46ch;
  opacity: 0.8;
}

/* A filled div rather than a border, so the exporter emits it as a shape
   with a solid fill instead of dropping it with the element's box. */
.rh-cover__accent {
  width: 4.5rem;
  height: 0.375rem;
  background: var(--rh-red);
  margin-bottom: 1.75rem;
}

.rh-on-red .rh-cover__accent {
  background: var(--rh-white);
}

.rh-cover__eyebrow {
  margin-bottom: 1rem;
}

.rh-on-dark .rh-cover__eyebrow,
.rh-on-red .rh-cover__eyebrow {
  color: var(--rh-white);
}

.rh-cover__meta {
  margin-top: 2.5rem;
  font-size: 1rem;
  opacity: 0.7;
}
</style>
