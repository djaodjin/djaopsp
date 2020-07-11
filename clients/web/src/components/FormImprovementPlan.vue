<template>
  <fragment>
    <v-container class="pa-0">
      <v-row>
        <v-col class="pt-0" cols="12" sm="6">
          <v-select
            v-model="selectedAreas"
            :items="areas"
            :menu-props="{ maxHeight: '380' }"
            label="Filter by Practice Category"
            multiple
            chips
            deletable-chips
            hide-details="auto"
          ></v-select>
        </v-col>
        <v-col class="py-0" cols="12" sm="6">
          <v-select
            class="mb-4"
            v-model="practiceValue"
            :items="practiceValueOptions"
            label="Filter by Practice Value"
            hide-details="true"
          ></v-select>
          <v-subheader class="range-label">Practice value range</v-subheader>
          <v-range-slider
            class="mx-6"
            v-model="practiceValueRange"
            :min="minPracticeValue"
            :max="maxPracticeValue"
            :tick-size="4"
            :tick-labels="practiceValueLabels"
          ></v-range-slider>
        </v-col>
        <v-col class="pt-0" cols="12" sm="6">
          <v-subheader class="range-label mb-8"
            >Implementation rate by other companies</v-subheader
          >
          <v-range-slider
            class="mx-6"
            v-model="implementationRange"
            step="5"
            hide-details
            thumb-label="always"
          >
            <template v-slot:thumb-label="{ value }">{{
              `${value}%`
            }}</template>
          </v-range-slider>
        </v-col>
        <v-col cols="12" sm="6">
          <button-primary class="mb-4" @click="findResults">
            Find Matching Results
          </button-primary>
        </v-col>
      </v-row>
    </v-container>
    <div v-if="searchDone">
      <matching-practices
        :planPractices="planPractices"
        :practices="matchingPractices"
        :valueKey="practiceValue"
        @practice:add="addPractice"
        @practice:remove="removePractice"
      />
    </div>
  </fragment>
</template>

<script>
import { PRACTICE_VALUES, PRACTICE_VALUE_CATEGORIES } from '../config'
import { Fragment } from 'vue-fragment'
import { getResults } from '../mocks/ip-results'
import MatchingPractices from '@/components/MatchingPractices'
import ButtonPrimary from '@/components/ButtonPrimary'

const DELTA = 5
const MIN_PRACTICE_VALUE = PRACTICE_VALUES[0].value
const MAX_PRACTICE_VALUE = PRACTICE_VALUES[PRACTICE_VALUES.length - 1].value

export default {
  name: 'FormImprovementPlan',

  props: ['planPractices'],

  methods: {
    addPractice(...args) {
      this.$emit('practice:add', ...args)
    },
    removePractice(...args) {
      this.$emit('practice:remove', ...args)
    },
    async findResults() {
      this.matchingPractices = await getResults({
        areas: this.selectedAreas,
        practiceValue: this.practiceValue,
        practiceValueRange: this.practiceValueRange,
        implementationRange: this.implementationRange,
      })
      this.searchDone = true
    },
  },

  data() {
    return {
      searchDone: false,
      selectedAreas: [],
      implementationRange: [0, 100],
      practiceValue: PRACTICE_VALUE_CATEGORIES[0].value,
      practiceValueOptions: PRACTICE_VALUE_CATEGORIES,
      practiceValueLabels: PRACTICE_VALUES.map((p) => p.label),
      minPracticeValue: MIN_PRACTICE_VALUE,
      maxPracticeValue: MAX_PRACTICE_VALUE,
      practiceValueRange: [MIN_PRACTICE_VALUE, MAX_PRACTICE_VALUE],
      areas: [
        { header: 'Environmental Targets' },
        { text: 'Energy Reduction', value: 'E1' },
        { text: 'GHG Emissions', value: 'E2' },
        { text: 'Water Usage', value: 'E3' },
        { text: 'Waste Reduction', value: 'E4' },
        { divider: true },
        { header: 'Business Areas' },
        { text: 'Governance & Management', value: 'B1' },
        { text: 'Engineering & Design', value: 'B2' },
        { text: 'Procurement', value: 'B3' },
        { text: 'Construction', value: 'B4' },
        { text: 'Office/Ground', value: 'B5' },
      ],
      matchingPractices: [],
    }
  },

  components: {
    Fragment,
    ButtonPrimary,
    MatchingPractices,
  },
}
</script>

<style lang="scss" scoped>
.range-label {
  height: 30px;
  padding-left: 0;
}
</style>
