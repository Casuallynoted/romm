import type { HeartbeatResponse } from "@/__generated__";
import { defineStore } from "pinia";
import { computed } from "vue";

export default defineStore("heartbeat", {
  state: () => {
    return { value: {} as HeartbeatResponse };
  },

  actions: {
    set(data: HeartbeatResponse) {
      this.value = data;
    },
    getMetadataOptions() {
      return computed(() => [
        {
          name: "IGDB",
          value: "igdb",
          disabled: !this.value.METADATA_SOURCES?.IGDB_API_ENABLED,
        },
        {
          name: "MobyGames",
          value: "moby",
          disabled: !this.value.METADATA_SOURCES?.MOBY_API_ENABLED,
        },
      ]).value.filter((s) => !s.disabled);
    },
  },
});
