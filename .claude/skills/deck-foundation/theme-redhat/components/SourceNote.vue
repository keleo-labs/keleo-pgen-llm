<!--
  The citation line at the foot of a content slide.

  Every layout that can carry evidence accepts a `sources` array and renders
  this. Entries are `{label, url}`; the url is optional, so an unlinkable
  source ("Internal adoption review, 2026") still gets attributed.

    ---
    layout: columns
    sources:
      - label: Hellekson, 2026
        url: https://www.redhat.com/en/blog/lightwell-reality-check
      - label: OpenSSF, 2024
        url: https://slsa.dev
    ---

  Why a foot band rather than links inside the body copy: Google Slides
  rewrites link runs to its own HYPERLINK theme colour and forces an
  underline on import, overriding whatever the theme set. Inline links
  therefore punch blue holes through body text and the slide stops looking
  branded. Confined to a small muted line at the foot, blue-underlined text
  reads as a citation, which is what it is.

  That same restyling is why sources belong on light slides only. On the
  dark and red variants the imposed link blue has too little contrast to
  read — and covers, section dividers, statements and closings should not be
  carrying citations anyway.
-->
<script setup lang="ts">
interface Source {
  label: string
  url?: string
}

defineProps<{
  sources?: Source[]
}>()
</script>

<template>
  <div v-if="sources?.length" class="rh-sources">
    <template v-for="(source, i) in sources" :key="i">
      <span v-if="i > 0" class="rh-sources__sep"> · </span>
      <a v-if="source.url" :href="source.url" target="_blank" rel="noopener">{{ source.label }}</a>
      <span v-else>{{ source.label }}</span>
    </template>
  </div>
</template>

<style scoped>
/* The gap is clearance, not decoration: PowerPoint sets the content above
   this line in a taller box than Chromium measured, and without the slack
   that content lands on top of the citation. See DECK-FOUNDATION.md §4. */
.rh-sources {
  margin-top: 1.75rem;
  font-size: 0.8125rem;
  line-height: 1.4;
  color: var(--rh-grey-text);
}

.rh-sources a {
  color: var(--rh-link);
  text-decoration: underline;
}

.rh-sources__sep {
  color: var(--rh-grey-text);
}
</style>
