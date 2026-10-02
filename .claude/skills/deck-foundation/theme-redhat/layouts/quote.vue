<!--
  A pull quote carrying someone else's authority. Keep it verbatim — a
  paraphrase in quotation marks is a misattribution.

  ---
  layout: quote
  attribution: Platform lead, European retail bank
  variant: dark
  ---
  The second team is where you find out whether you built a platform
  or just a very good environment for one team.
-->
<script setup lang="ts">
interface Source {
  label: string
  url?: string
}

const props = withDefaults(
  defineProps<{
    variant?: 'light' | 'dark' | 'red'
    attribution?: string
    role?: string
    sources?: Source[]
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
  <div class="slidev-layout rh-quote" :class="surface">
    <div class="rh-quote__mark">&ldquo;</div>
    <div class="rh-quote__body">
      <slot />
    </div>
    <div v-if="attribution" class="rh-quote__attribution">
      {{ attribution }}<template v-if="role">, {{ role }}</template>
    </div>
    <SourceNote :sources="sources" />
  </div>
</template>

<style scoped>
.rh-quote {
  display: flex;
  flex-direction: column;
  justify-content: center;
  height: 100%;
}

/* A real character rather than a pseudo-element, so it exports as text. */
.rh-quote__mark {
  font-family: var(--rh-font-display);
  font-size: 5rem;
  font-weight: 700;
  line-height: 0.6;
  color: var(--rh-red);
  margin-bottom: 1.25rem;
}

.rh-on-dark .rh-quote__mark,
.rh-on-red .rh-quote__mark {
  color: var(--rh-white);
}

.rh-quote__body :deep(p) {
  font-family: var(--rh-font-display);
  font-size: 2.25rem;
  font-weight: 500;
  line-height: 1.28;
  margin: 0;
  max-width: 30ch;
}

.rh-quote__attribution {
  margin-top: 2rem;
  font-family: var(--rh-font-text);
  font-size: 1.0625rem;
  opacity: 0.75;
}
</style>
