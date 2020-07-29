<template>
  <v-sheet class="py-3 px-2 mt-6" elevation="3">
    <sheet-title>Practice Value by Domain</sheet-title>
    <chart-practice-values-aggregate class="mt-4 mx-4" :practices="practices" />
  </v-sheet>
</template>

<script>
import { PRACTICE_VALUE_CATEGORY_DEFAULT } from '@/config/app'
import SheetTitle from '@/components/SheetTitle'
import ChartPracticeValuesAggregate from '@/components/ChartPracticeValuesAggregate'

export default {
  name: 'ScorecardPracticesChart',

  props: ['practices'],

  components: {
    SheetTitle,
    ChartPracticeValuesAggregate,
  },
}
</script>

<style lang="scss" scoped></style>
