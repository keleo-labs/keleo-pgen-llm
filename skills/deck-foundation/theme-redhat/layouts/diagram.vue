<!--
  A diagram filling the slide under an assertion title.

  `diagram` names a spec in the format render-diagram.py reads. The build step
  (`build-diagrams.py`) renders it to a PNG beside the spec and fits it to the
  slide's aspect; this layout shows that PNG, so the local preview and a
  --pptx-only export are already correct.

  After publishing, publish-deck.py replaces the picture with native Google
  Slides shapes, which are editable in the deck. The marker caption is how it
  finds this slide — it is removed in the same pass, and left in place when
  the upgrade is skipped, where it reads as a quiet provenance note.

  ---
  layout: diagram
  diagram: ./assets/option-a-topology.json
  ---
  # Remediation runs on a schedule

  For an image with no spec — a screenshot or a photo — use `image` instead
  and no shape pass is attempted.
-->
<script setup lang="ts">
interface Source {
  label: string
  url?: string
}

const props = withDefaults(
  defineProps<{
    diagram?: string
    image?: string
    imageAlt?: string
    eyebrow?: string
    sources?: Source[]
  }>(),
  {},
)

// Spec and rendering live side by side: build-diagrams.py writes <stem>.png
// next to <stem>.json, so the layout needs no second path to be kept in sync.
const src = props.image || (props.diagram ? props.diagram.replace(/\.json$/, '.png') : '')
const marker = props.diagram
  ? props.diagram.split('/').pop()!.replace(/\.json$/, '')
  : ''
</script>

<template>
  <div class="slidev-layout rh-diagram">
    <div v-if="eyebrow" class="rh-diagram__eyebrow">{{ eyebrow }}</div>
    <slot />
    <div class="rh-diagram__frame">
      <img v-if="src" :src="src" :alt="imageAlt || ''" class="rh-diagram__image" />
    </div>
    <div v-if="marker" class="rh-diagram__marker">diagram:{{ marker }}</div>
    <SourceNote :sources="sources" />
  </div>
</template>

<style scoped>
.rh-diagram {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.rh-diagram__eyebrow {
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--rh-grey-text);
  margin-bottom: 0.25rem;
}

/* The frame takes the remaining height so the image is sized by the slide
   rather than by its own pixel dimensions. */
.rh-diagram__frame {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0.5rem 0;
}

.rh-diagram__image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.rh-diagram__marker {
  font-size: 0.5rem;
  color: var(--rh-grey-text);
  opacity: 0.55;
}
</style>
