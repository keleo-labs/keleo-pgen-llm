<!--
  Section divider. Resets the audience's attention between movements of the
  argument; carries a number so a long deck stays navigable.
-->
<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: 'red' | 'dark' | 'light'
    number?: string | number
  }>(),
  { variant: 'red' },
)

const surface = {
  red: 'rh-on-red',
  dark: 'rh-on-dark',
  light: '',
}[props.variant]
</script>

<template>
  <div class="slidev-layout rh-section" :class="surface">
    <div v-if="number !== undefined" class="rh-section__number">
      {{ String(number).padStart(2, '0') }}
    </div>
    <div class="rh-section__body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.rh-section {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

/* Opacity rather than a colour would sink this into the red fill, so each
   surface gets an explicit tone. */
.rh-section__number {
  font-family: var(--rh-font-display);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--rh-red);
  margin-bottom: 0.75rem;
}

.rh-on-red .rh-section__number,
.rh-on-dark .rh-section__number {
  color: var(--rh-white);
}

.rh-section__body :deep(h1) {
  font-family: var(--rh-font-display);
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.02em;
  margin: 0;
  max-width: 22ch;
}

.rh-section__body :deep(p) {
  font-size: 1.375rem;
  line-height: 1.4;
  margin: 1rem 0 0 0;
  max-width: 50ch;
  opacity: 0.85;
}
</style>
