<template>
  <v-sheet class="px-2 mt-6" elevation="3">
    <v-list>
      <sheet-title>Score by Business Area</sheet-title>
      <v-list-item
        two-line
        v-for="(benchmark, i) in benchmarks"
        :key="i"
        :inactive="true"
      >
        <v-list-item-avatar tile>
          <img
            class="d-inline-block"
            height="48"
            width="48"
            alt
            :src="benchmark.section.iconPath"
          />
        </v-list-item-avatar>
        <v-list-item-content>
          <v-list-item-title>{{ benchmark.section.name }}</v-list-item-title>
          <v-list-item-title>
            Score: <b>{{ benchmark.companyScore }}%</b>
          </v-list-item-title>
          <v-list-item-subtitle>
            Total Score Coefficient: <b>{{ benchmark.scoreCoefficient }}</b>
          </v-list-item-subtitle>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </v-sheet>
</template>

<script>
import SheetTitle from '@/components/SheetTitle'

export default {
  name: 'ScorecardBusinessAreas',

  props: ['benchmarks'],

  components: {
    SheetTitle,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.v-list-item--two-line
  .v-list-item__avatar:not(.v-list-item__avatar--horizontal) {
  margin-bottom: 4px;
  margin-top: 4px;
  align-self: center;
}
img {
  border-radius: 3px;
  padding: 3px;
  background-color: $background-icon;
}
</style>
