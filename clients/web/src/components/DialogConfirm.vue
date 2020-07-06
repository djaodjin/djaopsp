<template>
  <v-dialog v-model="isOpen" persistent max-width="520">
    <v-card>
      <v-card-title class="headline pb-4 text-center">
        <span style="flex: 1;">{{ title }}</span>
      </v-card-title>
      <v-card-text class="pt-0 pb-2 text-body-2 text-body-2-sm">
        <slot></slot>
      </v-card-text>
      <div class="actions px-6 pb-5">
        <button-primary class="mb-4" @click="$emit('confirm')">
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

  props: ['isOpen', 'actionText', 'title'],

  components: {
    ButtonPrimary,
  },
}
</script>
