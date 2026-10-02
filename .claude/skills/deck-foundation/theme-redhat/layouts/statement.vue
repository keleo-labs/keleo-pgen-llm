<!--
  One claim, nothing else. Use at the hinge points of an argument, where the
  audience should be listening rather than reading.

  Deliberately offers no body slot: if the claim needs support on the same
  slide, it is not a statement slide.
-->
<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: 'light' | 'dark' | 'red'
    attribution?: string
  }>(),
  { variant: 'light' },
)

const surface = {
  light: '',
  dark: 'rh-on-dark',
  red: 'rh-on-red',
}[props.variant]
</script>

<template>
  <div class="slidev-layout rh-statement" :class="surface">
    <div class="rh-statement__body">
      <slot />
    </div>
    <div v-if="attribution" class="rh-statement__attribution">
      {{ attribution }}
    </div>
  </div>
</template>

<style scoped>
.rh-statement {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

.rh-statement__body :deep(h1),
.rh-statement__body :deep(p) {
  font-family: var(--rh-font-display);
  font-size: 4.25rem;
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.02em;
  margin: 0;
  /* Narrow enough that a one-line claim breaks to two and fills the slide —
     a statement that sits on a single thin line reads as a subtitle. */
  max-width: 16ch;
}

.rh-statement__attribution {
  margin-top: 2rem;
  font-family: var(--rh-font-text);
  font-size: 1.125rem;
  opacity: 0.7;
}
</style>
