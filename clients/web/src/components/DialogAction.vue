<template>
  <v-dialog v-model="isOpen" persistent max-width="520">
    <v-card>
      <v-card-title class="headline pb-4">{{ title }}</v-card-title>
      <v-card-text class="pt-0 pb-2 text-body-2 text-body-2-sm">
        <slot></slot>
      </v-card-text>
      <div class="actions px-6 pb-5">
        <button-primary class="mb-4" @click="$emit('action')">
          {{ actionText }}
        </button-primary>
        <button-secondary @click="$emit('cancel')">Cancel</button-secondary>
      </div>
    </v-card>
  </v-dialog>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'
import ButtonSecondary from '@/components/ButtonSecondary'

export default {
  name: 'IntroSection',

  props: ['isOpen', 'actionText', 'title'],

  components: {
    ButtonPrimary,
    ButtonSecondary,
  },
}
</script>
