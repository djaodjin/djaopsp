<template>
  <v-sheet class="py-3 px-2 mt-6" elevation="3">
    <sheet-title>Environmental Targets</sheet-title>
    <ul class="target-list pl-4 pr-2">
      <li class="target pt-2 pb-3" v-for="target in targets" :key="target.key">
        <h4 class="mb-1">{{ ASSESSMENT_TARGETS_LABELS[target.key] }}</h4>
        <p class="mb-0">
          {{ target.text }}
        </p>
      </li>
    </ul>
  </v-sheet>
</template>

<script>
import { ASSESSMENT_TARGETS_LABELS } from '@/config/app'
import SheetTitle from '@/components/SheetTitle'

export default {
  name: 'ScorecardTargets',

  props: ['targets'],

  data() {
    return {
      ASSESSMENT_TARGETS_LABELS,
    }
  },

  components: {
    SheetTitle,
  },
}
</script>

<style lang="scss" scoped>
.target-list {
  overflow: hidden;
}
.target {
  @media #{map-get($display-breakpoints, 'xl-only')} {
    padding-right: 3%;
    width: 50%;
    float: left;
  }

  h4 {
    font-size: 1rem;
  }
  small {
    font-size: 0.9rem;
  }
}
</style>
