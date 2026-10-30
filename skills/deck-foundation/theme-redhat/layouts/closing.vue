<!--
  The ask. A deck that ends on "Thank you" wastes its last slide — this one
  expects the specific next action and who owns it.

  ---
  layout: closing
  actions:
    - Fund a platform product owner for FY27
    - Pick the second adopting team by March
  contact: ed@example.com
  ---
  # Decide the owner, and the rest follows
-->
<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: 'dark' | 'red' | 'light'
    actions?: string[]
    contact?: string
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
  <div class="slidev-layout rh-closing" :class="surface">
    <div class="rh-closing__body">
      <slot />
    </div>
    <ol v-if="actions?.length" class="rh-closing__actions">
      <li v-for="(action, i) in actions" :key="i">{{ action }}</li>
    </ol>
    <div v-if="contact" class="rh-closing__contact">{{ contact }}</div>
  </div>
</template>

<style scoped>
.rh-closing {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

.rh-closing__body :deep(h1) {
  font-family: var(--rh-font-display);
  font-size: 3.25rem;
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.02em;
  margin: 0;
  max-width: 22ch;
}

/* The CSS reset clears list markers, so decimal is restored explicitly —
   real markers export as numbered paragraphs rather than flat text. */
.rh-closing__actions {
  list-style: decimal;
  /* Clears the display-size title's descenders after conversion, where
     PowerPoint sets the same heading in a taller box — DECK-FOUNDATION §4. */
  margin: 3.25rem 0 0 0;
  padding-left: 1.75rem;
  max-width: 48ch;
}

.rh-closing__actions li {
  font-size: 1.25rem;
  line-height: 1.45;
  margin-bottom: 0.75rem;
}

.rh-closing__actions li::marker {
  font-family: var(--rh-font-display);
  font-weight: 700;
  color: var(--rh-red);
}

.rh-on-dark .rh-closing__actions li::marker,
.rh-on-red .rh-closing__actions li::marker {
  color: var(--rh-white);
}

.rh-closing__contact {
  margin-top: 2.25rem;
  font-size: 1rem;
  opacity: 0.7;
}
</style>
