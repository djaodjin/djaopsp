<template>
  <div class="text-center" v-if="results.length">
    <h3 class="mb-1 text-h6">Matching Practices: {{ results.length }}</h3>
    <p>Select practices to add to your improvement plan</p>
    <v-data-table
      class="results"
      :headers="headers"
      :items="results"
      :sort-by="['value', 'implementation']"
      :sort-desc="[true, false]"
      multi-sort
      must-sort
      disable-pagination
      disable-filtering
      hide-default-footer
      @click:row="selectPractice"
    >
      <template v-slot:item.implementation="{ value }">
        <span>{{ `${value}%` }}</span>
      </template>
      <template v-slot:item.text="{ value }">
        <p class="clamped mb-0">
          {{ value }}
        </p>
      </template>
    </v-data-table>
  </div>
  <div class="text-center" v-else>
    <h3 class="mb-1 text-h6">No Results Found</h3>
    <p>Change the search filters and try again</p>
  </div>
</template>

<script>
export default {
  name: 'MatchingPractices',

  props: ['results'],

  methods: {
    selectPractice() {
      console.log('Practice selected')
    },
  },

  data() {
    return {
      headers: [
        {
          text: 'Value',
          align: 'start',
          value: 'value',
          filterable: false,
        },
        {
          text: 'Implementation Rate',
          value: 'implementation',
          filterable: false,
        },
        {
          text: 'Practice Name',
          value: 'text',
          sortable: false,
          filterable: false,
        },
      ],
    }
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.results {
  & ::v-deep .v-data-table__mobile-table-row {
    &:nth-child(even) .v-data-table__mobile-row {
      background-color: $background-row-alternate;
    }
  }
  & ::v-deep .v-data-table__mobile-row {
    min-height: 36px;
    height: 36px;

    & > .v-data-table__mobile-row__cell {
      text-align: left;
      width: 55%;
    }

    &:last-child {
      min-height: 76px;
      height: 76px;
      align-items: flex-start;
      padding-top: 4px;

      & > .v-data-table__mobile-row__cell {
        width: 65%;
      }
    }
  }

  .clamped {
    color: $primary-color;
    text-decoration: underline;
    cursor: pointer;
    text-align: left;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 3;
    overflow: hidden;
  }
}
</style>
