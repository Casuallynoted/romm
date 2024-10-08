<script setup lang="ts">
import collectionApi, {
  type UpdatedCollection,
} from "@/services/api/collection";
import storeAuth from "@/stores/auth";
import storeCollections, { type Collection } from "@/stores/collections";
import storeHeartbeat from "@/stores/heartbeat";
import type { SimpleRom } from "@/stores/roms";
import storeRoms from "@/stores/roms";
import type { Events } from "@/types/emitter";
import type { Emitter } from "mitt";
import { storeToRefs } from "pinia";
import { inject } from "vue";

// Props
const props = defineProps<{ rom: SimpleRom }>();
const emitter = inject<Emitter<Events>>("emitter");
const heartbeat = storeHeartbeat();
const auth = storeAuth();
const collectionsStore = storeCollections();
const romsStore = storeRoms();
const { favCollection } = storeToRefs(collectionsStore);

// Functions
async function switchFromFavourites() {
  if (!favCollection.value) {
    await collectionApi
      .createCollection({
        collection: { name: "Favourites" } as UpdatedCollection,
      })
      .then(({ data }) => {
        collectionsStore.add(data);
        favCollection.value = data;
        emitter?.emit("snackbarShow", {
          msg: `Collection ${data.name} created successfully!`,
          icon: "mdi-check-bold",
          color: "green",
          timeout: 2000,
        });
      })
      .catch((error) => {
        console.log(error);
        emitter?.emit("snackbarShow", {
          msg: error.response.data.detail,
          icon: "mdi-close-circle",
          color: "red",
        });
        return;
      });
  }
  if (!collectionsStore.isFav(props.rom)) {
    favCollection.value?.roms.push(props.rom.id);
  } else {
    if (favCollection.value) {
      favCollection.value.roms = favCollection.value.roms.filter(
        (id) => id !== props.rom.id
      );
      if (romsStore.currentCollection?.name.toLowerCase() == "favourites") {
        romsStore.remove([props.rom]);
      }
    }
  }
  await collectionApi
    .updateCollection({ collection: favCollection.value as Collection })
    .then(({ data }) => {
      emitter?.emit("snackbarShow", {
        msg: `${props.rom.name} ${
          collectionsStore.isFav(props.rom) ? "added to" : "removed from"
        } ${favCollection.value?.name} successfully!`,
        icon: "mdi-check-bold",
        color: "green",
        timeout: 2000,
      });
    })
    .catch((error) => {
      console.log(error);
      emitter?.emit("snackbarShow", {
        msg: error.response.data.detail,
        icon: "mdi-close-circle",
        color: "red",
      });
      return;
    })
    .finally(() => {
      emitter?.emit("showLoadingDialog", { loading: false, scrim: false });
    });
}
</script>

<template>
  <v-list rounded="0" class="pa-0">
    <template v-if="auth.scopes.includes('roms.write')">
      <v-list-item
        :disabled="!heartbeat.value.ANY_SOURCE_ENABLED"
        class="py-4 pr-5"
        @click="emitter?.emit('showMatchRomDialog', rom)"
      >
        <v-list-item-title class="d-flex">
          <v-icon icon="mdi-search-web" class="mr-2" />Manual match
        </v-list-item-title>
        <v-list-item-subtitle>
          {{
            !heartbeat.value.ANY_SOURCE_ENABLED
              ? "No metadata source enabled"
              : ""
          }}
        </v-list-item-subtitle>
      </v-list-item>
      <v-list-item
        class="py-4 pr-5"
        @click="emitter?.emit('showEditRomDialog', { ...rom })"
      >
        <v-list-item-title class="d-flex">
          <v-icon icon="mdi-pencil-box" class="mr-2" />Edit
        </v-list-item-title>
      </v-list-item>
      <v-divider />
    </template>
    <v-list-item
      v-if="auth.scopes.includes('collections.write')"
      class="py-4 pr-5"
      @click="switchFromFavourites"
    >
      <v-list-item-title class="d-flex">
        <v-icon
          :icon="collectionsStore.isFav(rom) ? 'mdi-star-outline' : 'mdi-star'"
          class="mr-2"
        />{{
          `${collectionsStore.isFav(rom) ? "Remove from" : "Add to"} favourites`
        }}
      </v-list-item-title>
    </v-list-item>
    <v-list-item
      v-if="auth.scopes.includes('collections.write')"
      class="py-4 pr-5"
      @click="emitter?.emit('showAddToCollectionDialog', [{ ...rom }])"
    >
      <v-list-item-title class="d-flex">
        <v-icon icon="mdi-bookmark-plus-outline" class="mr-2" />Add to
        collection
      </v-list-item-title>
    </v-list-item>
    <template v-if="auth.scopes.includes('roms.write')">
      <v-divider />
      <v-list-item
        class="py-4 pr-5 text-romm-red"
        @click="emitter?.emit('showDeleteRomDialog', [rom])"
      >
        <v-list-item-title class="d-flex">
          <v-icon icon="mdi-delete" class="mr-2" />Delete
        </v-list-item-title>
      </v-list-item>
    </template>
  </v-list>
</template>
