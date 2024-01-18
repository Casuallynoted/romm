<script setup lang="ts">
import { ref, inject } from "vue";
import { useDisplay } from "vuetify";
import type { Emitter } from "mitt";
import type { Events } from "@/types/emitter";

import storeRoms from "@/stores/roms";
import api_save from "@/services/api_save";
import api_state from "@/services/api_state";
import type { Rom } from "@/stores/roms";
import type { SaveSchema, StateSchema } from "@/__generated__";

const { xs, mdAndDown, lgAndUp } = useDisplay();
const romsStore = storeRoms();
const show = ref(false);
const assetType = ref<"saves" | "states">("saves");
const romRef = ref<Rom | null>(null);
const assets = ref<(SaveSchema | StateSchema)[]>([]);
const deleteFromFs = ref(false);

const emitter = inject<Emitter<Events>>("emitter");
emitter?.on("showDeleteSavesDialog", ({ rom, saves }) => {
  assetType.value = "saves";
  assets.value = saves;
  show.value = true;
  romRef.value = rom;
});
emitter?.on("showDeleteStatesDialog", ({ rom, states }) => {
  assetType.value = "states";
  assets.value = states;
  show.value = true;
  romRef.value = rom;
});

async function deleteAssets() {
  if (!assets.value) return;

  const result =
    (await assetType.value) === "saves"
      ? api_save.deleteSaves({
          saves: assets.value,
          deleteFromFs: deleteFromFs.value,
        })
      : api_state.deleteStates({
          states: assets.value,
          deleteFromFs: deleteFromFs.value,
        });

  result
    .then(({ data }) => {
      if (romRef.value) {
        romRef.value[assetType.value] = data;
        romsStore.update(romRef.value);
        emitter?.emit("romUpdated", romRef.value);
      }
    })
    .catch(({ response, message }) => {
      emitter?.emit("snackbarShow", {
        msg: `Unable to delete saves: ${
          response?.data?.detail || response?.statusText || message
        }`,
        icon: "mdi-close-circle",
        color: "red",
        timeout: 4000,
      });
    });

  closeDialog();
}

function closeDialog() {
  deleteFromFs.value = false;
  assets.value = [];
  show.value = false;
}
</script>

<template>
  <v-dialog
    :modelValue="show"
    width="auto"
    @click:outside="closeDialog"
    @keydown.esc="closeDialog"
    no-click-animation
    persistent
    :scrim="true"
  >
    <v-card
      rounded="0"
      :class="{
        'delete-content': lgAndUp,
        'delete-content-tablet': mdAndDown,
        'delete-content-mobile': xs,
      }"
    >
      <v-toolbar density="compact" class="bg-terciary">
        <v-row class="align-center" no-gutters>
          <v-col cols="9" xs="9" sm="10" md="10" lg="11">
            <v-icon icon="mdi-delete" class="ml-5" />
          </v-col>
          <v-col>
            <v-btn
              @click="closeDialog"
              class="bg-terciary"
              rounded="0"
              variant="text"
              icon="mdi-close"
              block
            />
          </v-col>
        </v-row>
      </v-toolbar>
      <v-divider class="border-opacity-25" :thickness="1" />
      <v-card-text>
        <v-row class="justify-center pa-2" no-gutters>
          <span>Deleting the following</span>
          <span class="text-romm-accent-1 mx-1">{{ assets.length }}</span>
          <span>{{ assetType }}. Do you confirm?</span>
        </v-row>
      </v-card-text>
      <v-card-text class="scroll bg-terciary py-0">
        <v-row class="justify-center pa-2" no-gutters>
          <v-list class="bg-terciary py-0">
            <v-list-item
              v-for="asset in assets"
              class="justify-center bg-terciary"
            >
              {{ asset.file_name }}
            </v-list-item>
          </v-list>
        </v-row>
      </v-card-text>
      <v-card-text>
        <v-row class="justify-center pa-2" no-gutters>
          <v-btn @click="closeDialog" class="bg-terciary">Cancel</v-btn>
          <v-btn @click="deleteAssets()" class="text-romm-red bg-terciary ml-5"
            >Confirm</v-btn
          >
        </v-row>
      </v-card-text>

      <v-divider class="border-opacity-25" :thickness="1" />
      <v-toolbar class="bg-terciary" density="compact">
        <v-checkbox
          v-model="deleteFromFs"
          label="Remove from filesystem"
          class="ml-3"
          hide-details
        />
      </v-toolbar>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.delete-content {
  width: 900px;
  max-height: 600px;
}

.delete-content-tablet {
  width: 570px;
  max-height: 600px;
}

.delete-content-mobile {
  width: 85vw;
  max-height: 600px;
}
.scroll {
  overflow-y: scroll;
}
</style>