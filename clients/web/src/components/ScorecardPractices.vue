<template>
  <v-sheet class="py-3 px-2" elevation="3">
    <sheet-title>Improvement Plan</sheet-title>
    <ul class="practices-list pl-4 pr-3">
      <li
        class="practice pt-2 pb-4"
        v-for="practice in practices"
        :key="practice.id"
      >
        <practice-overview
          :practice="practice"
          :valueCategory="defaultCategory"
        />
      </li>
    </ul>
  </v-sheet>
</template>

<script>
import { PRACTICE_VALUE_CATEGORY_DEFAULT } from '@/config/app'
import PracticeOverview from '@/components/PracticeOverview'
import SheetTitle from '@/components/SheetTitle'

export default {
  name: 'ScorecardPractices',

  props: ['practices'],

  data() {
    return {
      defaultCategory: PRACTICE_VALUE_CATEGORY_DEFAULT,
    }
  },

  components: {
    PracticeOverview,
    SheetTitle,
  },
}
</script>

<style lang="scss" scoped>
.practices-list {
  overflow: hidden;
}
.practice {
  @media #{map-get($display-breakpoints, 'xl-only')} {
    padding-right: 3%;
    width: 50%;
    float: left;
  }
}
</style>
