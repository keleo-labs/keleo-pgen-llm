<!--
  The workhorse content slide: an assertion headline over supporting evidence.

  The headline is the argument and the body is the proof, so the h1 is given
  room and the body is capped in width to stop it sprawling into a wall of
  text. If a slide needs more than this layout holds, it is two slides.
-->
<script setup lang="ts">
interface Source {
  label: string
  url?: string
}

defineProps<{
  eyebrow?: string
  subhead?: string
  sources?: Source[]
}>()
</script>

<template>
  <div class="slidev-layout rh-default">
    <div v-if="eyebrow" class="rh-eyebrow">{{ eyebrow }}</div>
    <div class="rh-default__body">
      <slot />
    </div>
    <SourceNote :sources="sources" />
  </div>
</template>

<style scoped>
.rh-default {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.rh-default__body {
  flex: 1;
  min-height: 0;
}

/* The title occupies a reserved two-line zone rather than only the height
   its text happens to need. PowerPoint sets the same string slightly wider
   than Chromium, so a title that just fits one line here can wrap to two
   after conversion — and because the exporter has already frozen the body's
   position, that second line lands on top of it. Reserving the space makes
   the re-wrap harmless and aligns titles across the deck as a bonus.
   Titles longer than two lines defeat this; see DECK-FOUNDATION.md §4. */
.rh-default__body :deep(h1) {
  font-family: var(--rh-font-display);
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.01em;
  min-height: 2.3em;
  margin: 0 0 1.5rem 0;
  max-width: 22ch;
}

.rh-default__body :deep(h2) {
  font-family: var(--rh-font-display);
  font-size: 1.5rem;
  font-weight: 700;
  margin: 1.5rem 0 0.75rem 0;
}

.rh-default__body :deep(p) {
  font-size: 1.25rem;
  line-height: 1.5;
  margin: 0 0 1rem 0;
  max-width: 62ch;
}

/* Lists take the same measure cap as paragraphs. Uncapped they run the full
   slide width — a ~140-character line that is uncomfortable to read and
   visibly inconsistent with the 24ch headline above it. */
.rh-default__body :deep(ul),
.rh-default__body :deep(ol) {
  max-width: 62ch;
}

.rh-default__body :deep(li) {
  font-size: 1.1875rem;
  margin-bottom: 0.9rem;
}
</style>
