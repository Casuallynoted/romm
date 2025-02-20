<script setup lang="ts">
import type { Collection } from "@/stores/collections";
import storeGalleryView from "@/stores/galleryView";
import { getCollectionCoverImage, getFavoriteCoverImage } from "@/utils/covers";
import { computed } from "vue";

// Props
const props = withDefaults(
  defineProps<{
    collection: Collection;
    transformScale?: boolean;
    titleOnHover?: boolean;
    showRomCount?: boolean;
    withLink?: boolean;
    src?: string;
  }>(),
  {
    transformScale: false,
    titleOnHover: false,
    showRomCount: false,
    withLink: false,
    src: "",
  },
);

const galleryViewStore = storeGalleryView();
const collectionCoverImage = computed(() =>
  getCollectionCoverImage(props.collection.name),
);
const favoriteCoverImage = computed(() =>
  getFavoriteCoverImage(props.collection.name),
);
</script>

<template>
  <v-hover v-slot="{ isHovering, props: hoverProps }">
    <v-card
      v-bind="{
        ...hoverProps,
        ...(withLink && collection
          ? {
              to: { name: 'collection', params: { collection: collection.id } },
            }
          : {}),
      }"
      :class="{
        'on-hover': isHovering,
        'transform-scale': transformScale,
      }"
      :elevation="isHovering && transformScale ? 20 : 3"
    >
      <v-img
        cover
        :src="
          src
            ? src
            : collection.has_cover
              ? `/assets/romm/resources/${collection.path_cover_l}?ts=${collection.updated_at}`
              : collection.name && collection.name.toLowerCase() == 'favourites'
                ? favoriteCoverImage
                : collectionCoverImage
        "
        :lazy-src="
          src
            ? src
            : collection.has_cover
              ? `/assets/romm/resources/${collection.path_cover_s}?ts=${collection.updated_at}`
              : collection.name && collection.name.toLowerCase() == 'favourites'
                ? favoriteCoverImage
                : collectionCoverImage
        "
        :aspect-ratio="galleryViewStore.defaultAspectRatioCollection"
      >
        <template v-if="titleOnHover">
          <v-expand-transition>
            <div
              v-if="isHovering || !collection.has_cover"
              class="translucent-dark text-caption text-center text-white"
            >
              <v-list-item>{{ collection.name }}</v-list-item>
            </div>
          </v-expand-transition>
        </template>

        <div class="position-absolute append-inner">
          <slot name="append-inner"></slot>
        </div>

        <template #error>
          <v-img
            :src="collectionCoverImage"
            cover
            :aspect-ratio="galleryViewStore.defaultAspectRatioCollection"
          />
        </template>
        <template #placeholder>
          <div class="d-flex align-center justify-center fill-height">
            <v-progress-circular
              :width="2"
              :size="40"
              color="primary"
              indeterminate
            />
          </div>
        </template>
      </v-img>
      <v-chip
        v-if="showRomCount"
        class="bg-background position-absolute"
        size="x-small"
        style="bottom: 0.5rem; right: 0.5rem"
        label
      >
        {{ collection.rom_count }}
      </v-chip>
    </v-card>
  </v-hover>
</template>
<style scoped>
.append-inner {
  bottom: 0rem;
  right: 0rem;
}
</style>
