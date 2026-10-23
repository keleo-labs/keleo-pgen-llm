<!--
  Two unequal halves: narrative on one side, evidence on the other. Use for a
  claim beside its chart, table or image, where the two need to be read
  together rather than in sequence.

  The right half is a named slot, so markdown fills it:

  ---
  layout: split
  ---
  # Cost per environment fell by half

  Self-service removed the ticket queue entirely.

  ::right::

  ![Cost trend](https://example.com/chart.png)
-->
<script setup lang="ts">
interface Source {
  label: string
  url?: string
}

withDefaults(
  defineProps<{
    ratio?: 'even' | 'wide-left' | 'wide-right'
    image?: string
    imageAlt?: string
    sources?: Source[]
  }>(),
  { ratio: 'even' },
)

const columns = {
  even: '1fr 1fr',
  'wide-left': '1.4fr 1fr',
  'wide-right': '1fr 1.4fr',
}
</script>

<template>
  <div class="slidev-layout rh-split">
    <div class="rh-split__grid" :style="{ gridTemplateColumns: columns[ratio] }">
      <div class="rh-split__left">
        <slot />
      </div>
      <div class="rh-split__right">
        <img v-if="image" :src="image" :alt="imageAlt || ''" class="rh-split__image" />
        <slot v-else name="right" />
      </div>
    </div>
    <SourceNote :sources="sources" />
  </div>
</template>

<style scoped>
/* The grid is nested inside a column flex rather than being the root, so the
   citation line has somewhere to sit without becoming a third grid track. */
.rh-split {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.rh-split__grid {
  display: grid;
  gap: 3rem;
  align-items: center;
  flex: 1;
  min-height: 0;
}

.rh-split__left :deep(h1) {
  font-family: var(--rh-font-display);
  font-size: 2.25rem;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.01em;
  margin: 0 0 1.25rem 0;
}

.rh-split__left :deep(p) {
  font-size: 1.125rem;
  line-height: 1.55;
  margin: 0 0 0.875rem 0;
}

.rh-split__image {
  width: 100%;
  height: auto;
  display: block;
}
</style>
