<template>
  <v-chip class="practice-value" v-bind="$attrs" :color="valueColor">
    {{ valueLabel }}
  </v-chip>
</template>

<script>
import { PRACTICE_VALUES } from '@/config/app'

export default {
  name: 'PracticeValueChip',

  props: ['value'],

  computed: {
    valueItem() {
      return PRACTICE_VALUES.find((v) => v.value === this.value)
    },
    valueLabel() {
      return this.valueItem.label
    },
    valueColor() {
      return this.valueItem.color
    },
  },
}
</script>

<style lang="scss" scoped>
.practice-value {
  font-size: 1rem;
}
</style>
