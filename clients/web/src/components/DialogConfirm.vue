<template>
  <v-dialog v-model="showDialog" persistent max-width="520">
    <v-card>
      <v-card-title class="headline pb-4 text-center">
        <span style="flex: 1;">{{ title }}</span>
      </v-card-title>
      <v-card-text class="pt-0 pb-2 text-body-2 text-body-2-sm">
        <slot></slot>
      </v-card-text>
      <div class="actions px-6 pb-5">
        <button-primary class="mb-4" @click="closeAndSaveAsViewed">
          {{ actionText }}
        </button-primary>
      </div>
    </v-card>
  </v-dialog>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'DialogConfirm',

  props: [
    'storageKey',
    'showValue',
    'showFunctionAsync',
    'actionText',
    'title',
  ],

  methods: {
    closeAndSaveAsViewed() {
      window.localStorage.setItem(this.storageKey, 'viewed')
      this.showDialog = false
    },

    async initDialog() {
      const wasViewed = window.localStorage.getItem(this.storageKey)
      if (!wasViewed) {
        if (typeof this.showValue === 'undefined') {
          this.showDialog = await this.showFunctionAsync()
        } else {
          this.showDialog = this.showValue
        }
      }
    },
  },

  created() {
    this.initDialog()
  },

  data() {
    return {
      showDialog: false,
    }
  },

  components: {
    ButtonPrimary,
  },
}
</script>
