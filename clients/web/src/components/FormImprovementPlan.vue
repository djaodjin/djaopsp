<template>
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
          hide-details="true"
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
        <v-subheader class="range-label">Practice Value Range</v-subheader>
        <v-range-slider
          class="mx-6"
          v-model="practiceValueRange"
          min="0"
          max="3"
          :tick-size="4"
          :tick-labels="practiceValueLabels"
        ></v-range-slider>
      </v-col>
      <v-col class="pt-0" cols="12" sm="6">
        <v-subheader class="range-label mb-8"
          >Implementation by other companies</v-subheader
        >
        <v-range-slider
          class="mx-6"
          v-model="implementationRange"
          step="5"
          hide-details
          thumb-label="always"
        >
          <template v-slot:thumb-label="{ value }">{{ `${value}%` }}</template>
        </v-range-slider>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
const DELTA = 5

export default {
  name: 'FormImprovementPlan',

  data() {
    return {
      selectedAreas: [],
      implementationRange: [0, 100],
      practiceValue: null,
      practiceValueOptions: [
        { text: 'Average Value', value: 'average' },
        { text: 'Environmental Value', value: 'environmental' },
        { text: 'Cost Savings', value: 'financial' },
        { text: 'Operational Benefits', value: 'maintenance' },
      ],
      practiceValueLabels: ['Low', 'Medium', 'High', 'Gold'],
      practiceValueRange: [0, 3],
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
    }
  },
}
</script>

<style lang="scss" scoped>
.range-label {
  height: 30px;
  padding-left: 0;
}
</style>
