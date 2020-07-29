<template>
  <v-sheet class="py-3 px-2 mt-6" elevation="3">
    <sheet-title>Environmental Targets</sheet-title>
    <ul class="target-list pl-4">
      <li class="target pt-2 pb-4" v-for="target in targets" :key="target.id">
        <h4 class="mb-2">{{ target.category }}</h4>
        <p class="mb-1">
          <b>By {{ target.deadlineDate }}</b
          >: {{ target.text }}
        </p>
        <small>Baseline: {{ target.baselineDate }}</small>
      </li>
    </ul>
  </v-sheet>
</template>

<script>
import SheetTitle from '@/components/SheetTitle'

export default {
  name: 'ScorecardTargets',

  props: ['targets'],

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
