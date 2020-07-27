<template>
  <v-sheet class="px-2 mt-5" elevation="3">
    <v-list>
      <sheet-title>Score by Business Area</sheet-title>
      <v-list-item two-line v-for="(item, i) in data" :key="i" :inactive="true">
        <v-list-item-avatar tile>
          <v-img :src="`${publicPath}${item.icon}`" alt=""></v-img>
        </v-list-item-avatar>
        <v-list-item-content>
          <v-list-item-title>{{ item.name }}</v-list-item-title>
          <v-list-item-title>
            Score: <b>{{ item.score }}%</b>
          </v-list-item-title>
          <v-list-item-subtitle>
            Total Score Coefficient: <b>{{ item.coefficient }}</b>
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

  props: ['data'],

  data: () => ({
    publicPath: process.env.VUE_APP_ASSETS_URL || process.env.BASE_URL,
  }),

  components: {
    SheetTitle,
  },
}
</script>

<style lang="scss" scoped>
.v-list-item--two-line
  .v-list-item__avatar:not(.v-list-item__avatar--horizontal) {
  margin-bottom: 4px;
  margin-top: 4px;
  align-self: center;
}
</style>
