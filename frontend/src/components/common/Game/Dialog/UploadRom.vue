<script setup lang="ts">
import PlatformIcon from "@/components/common/Platform/Icon.vue";
import RDialog from "@/components/common/RDialog.vue";
import platformApi from "@/services/api/platform";
import romApi from "@/services/api/rom";
import socket from "@/services/socket";
import storeHeartbeat from "@/stores/heartbeat";
import { type Platform } from "@/stores/platforms";
import storeScanning from "@/stores/scanning";
import type { Events } from "@/types/emitter";
import { formatBytes } from "@/utils";
import type { Emitter } from "mitt";
import { inject, ref, watch } from "vue";
import { useDisplay } from "vuetify";

// Props
const { xs, mdAndUp, smAndUp } = useDisplay();
const show = ref(false);
const romsToUpload = ref<File[]>([]);
const scanningStore = storeScanning();
const selectedPlatform = ref<Platform | null>(null);
const supportedPlatforms = ref<Platform[]>();
const heartbeat = storeHeartbeat();
const HEADERS = [
  {
    title: "Name",
    align: "start",
    sortable: true,
    key: "name",
  },
  { title: "", align: "end", key: "actions", sortable: false },
] as const;
const page = ref(1);
const itemsPerPage = ref(10);
const pageCount = ref(0);
const PER_PAGE_OPTIONS = [10, 25, 50, 100];

const emitter = inject<Emitter<Events>>("emitter");
emitter?.on("showUploadRomDialog", (platformWhereUpload) => {
  if (platformWhereUpload) {
    selectedPlatform.value = platformWhereUpload;
  }
  show.value = true;
  platformApi
    .getSupportedPlatforms()
    .then(({ data }) => {
      supportedPlatforms.value = data.sort((a, b) => {
        return a.name.localeCompare(b.name);
      });
    })
    .catch(({ response, message }) => {
      emitter?.emit("snackbarShow", {
        msg: `Unable to upload roms: ${
          response?.data?.detail || response?.statusText || message
        }`,
        icon: "mdi-close-circle",
        color: "red",
        timeout: 4000,
      });
    });
});

// Functions
async function uploadRoms() {
  if (!selectedPlatform.value) return;
  show.value = false;
  scanningStore.set(true);

  if (selectedPlatform.value.id == -1) {
    await platformApi
      .uploadPlatform({ fsSlug: selectedPlatform.value.fs_slug })
      .then(({ data }) => {
        emitter?.emit("snackbarShow", {
          msg: `Platform ${selectedPlatform.value?.name} created successfully!`,
          icon: "mdi-check-bold",
          color: "green",
          timeout: 2000,
        });
        selectedPlatform.value = data;
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

  const platformId = selectedPlatform.value.id;
  emitter?.emit("snackbarShow", {
    msg: `Uploading ${romsToUpload.value.length} roms to ${selectedPlatform.value.name}...`,
    icon: "mdi-loading mdi-spin",
    color: "romm-accent-1",
  });

  await romApi
    .uploadRoms({
      romsToUpload: romsToUpload.value,
      platformId: platformId,
    })
    .then(({ data }) => {
      const { uploaded_roms, skipped_roms } = data;

      if (uploaded_roms.length == 0) {
        return emitter?.emit("snackbarShow", {
          msg: `All files skipped, nothing to upload.`,
          icon: "mdi-close-circle",
          color: "orange",
          timeout: 2000,
        });
      }

      emitter?.emit("snackbarShow", {
        msg: `${uploaded_roms.length} files uploaded successfully (and ${skipped_roms.length} skipped). Starting scan...`,
        icon: "mdi-check-bold",
        color: "green",
        timeout: 2000,
      });

      if (!socket.connected) socket.connect();
      setTimeout(() => {
        socket.emit("scan", {
          platforms: [platformId],
          type: "quick",
          apis: heartbeat.getMetadataOptions().map((s) => s.value),
        });
      }, 2000);
    })
    .catch(({ response, message }) => {
      emitter?.emit("snackbarShow", {
        msg: `Unable to upload roms: ${
          response?.data?.detail || response?.statusText || message
        }`,
        icon: "mdi-close-circle",
        color: "red",
        timeout: 4000,
      });
    });
  romsToUpload.value = [];
  selectedPlatform.value = null;
}

function triggerFileInput() {
  const fileInput = document.getElementById("file-input");
  fileInput?.click();
}

function removeRomFromList(romName: string) {
  romsToUpload.value = romsToUpload.value.filter((rom) => rom.name !== romName);
}

function closeDialog() {
  show.value = false;
  romsToUpload.value = [];
  selectedPlatform.value = null;
}

function updateDataTablePages() {
  pageCount.value = Math.ceil(romsToUpload.value.length / itemsPerPage.value);
}
watch(itemsPerPage, async () => {
  updateDataTablePages();
});
</script>

<template>
  <r-dialog
    @close="closeDialog"
    v-model="show"
    icon="mdi-upload"
    :width="mdAndUp ? '50vw' : '95vw'"
    scroll-content
  >
    <template #toolbar>
      <v-row class="align-center" no-gutters>
        <v-col cols="10" sm="8" lg="9">
          <v-autocomplete
            v-model="selectedPlatform"
            label="Platform"
            item-title="name"
            :items="supportedPlatforms"
            return-object
            clearable
            single-line
            hide-details
          >
            <template #item="{ props, item }">
              <v-list-item
                class="py-2"
                v-bind="props"
                :title="item.raw.name ?? ''"
              >
                <template #prepend>
                  <platform-icon
                    :key="item.raw.slug"
                    :size="35"
                    :slug="item.raw.slug"
                  />
                </template>
              </v-list-item>
            </template>
            <template #selection="{ item }">
              <v-list-item class="px-0" :title="item.raw.name ?? ''">
                <template #prepend>
                  <platform-icon
                    :size="35"
                    :key="item.raw.slug"
                    :slug="item.raw.slug"
                  />
                </template>
              </v-list-item>
            </template>
          </v-autocomplete>
        </v-col>
        <v-col>
          <v-btn
            block
            icon=""
            class="text-romm-accent-1 bg-terciary"
            rounded="0"
            variant="text"
            @click="triggerFileInput"
          >
            <v-icon :class="{ 'mr-2': !xs }"> mdi-plus </v-icon
            ><span v-if="!xs">Add</span>
          </v-btn>
          <v-file-input
            id="file-input"
            v-model="romsToUpload"
            @update:model-value="updateDataTablePages"
            class="file-input"
            multiple
            required
          />
        </v-col>
      </v-row>
    </template>
    <template #content>
      <v-data-table
        v-if="romsToUpload.length > 0"
        :item-value="(item) => item.name"
        :items="romsToUpload"
        :width="mdAndUp ? '60vw' : '95vw'"
        :items-per-page="itemsPerPage"
        :items-per-page-options="PER_PAGE_OPTIONS"
        :headers="HEADERS"
        v-model:page="page"
        hide-default-header
      >
        <template #item.name="{ item }">
          <v-list-item class="px-0">
            <v-row no-gutters>
              <v-col>
                {{ item.name }}
              </v-col>
            </v-row>
            <v-row no-gutters v-if="!smAndUp">
              <v-col>
                <v-chip size="x-small" label>{{
                  formatBytes(item.size)
                }}</v-chip>
              </v-col>
            </v-row>
            <template #append>
              <v-chip v-if="smAndUp" class="ml-2" size="x-small" label>{{
                formatBytes(item.size)
              }}</v-chip>
            </template>
          </v-list-item>
        </template>
        <template #item.actions="{ item }">
          <v-btn-group divided density="compact">
            <v-btn @click="removeRomFromList(item.name)">
              <v-icon class="text-romm-red"> mdi-close </v-icon>
            </v-btn>
          </v-btn-group>
        </template>
        <template #bottom>
          <v-divider />
          <v-row no-gutters class="pt-2 align-center justify-center">
            <v-col class="px-6">
              <v-pagination
                v-model="page"
                rounded="0"
                :show-first-last-page="true"
                active-color="romm-accent-1"
                :length="pageCount"
              />
            </v-col>
            <v-col cols="5" sm="3" xl="2">
              <v-select
                v-model="itemsPerPage"
                class="pa-2"
                label="Roms per page"
                density="compact"
                variant="outlined"
                :items="PER_PAGE_OPTIONS"
                hide-details
              />
            </v-col>
          </v-row>
        </template>
      </v-data-table>
    </template>
    <template #append>
      <v-row class="justify-center mb-2" no-gutters>
        <v-btn-group divided density="compact">
          <v-btn class="bg-terciary" @click="closeDialog"> Cancel </v-btn>
          <v-btn
            class="bg-terciary text-romm-green"
            :disabled="romsToUpload.length == 0 || selectedPlatform == null"
            :variant="
              romsToUpload.length == 0 || selectedPlatform == null
                ? 'plain'
                : 'flat'
            "
            @click="uploadRoms"
          >
            Upload
          </v-btn>
        </v-btn-group>
      </v-row>
    </template>
  </r-dialog>
</template>
