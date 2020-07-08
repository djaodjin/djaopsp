<template>
  <div class="text-center" v-if="results.length">
    <h3 class="mb-1 text-h6">Matching Practices: {{ results.length }}</h3>
    <p>Select practices to add to your improvement plan</p>
    <v-data-table
      :headers="headers"
      :items="results"
      :sort-by="['value', 'implementation']"
      :sort-desc="[true, false]"
      multi-sort
      must-sort
      disable-pagination
      disable-filtering
      hide-default-footer
    ></v-data-table>
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

  updated() {
    console.log(this.results)
  },

  data() {
    return {
      headers: [
        {
          text: 'Value',
          align: 'start',
          value: 'value',
        },
        { text: 'Implementation Rate', value: 'implementation' },
        { text: 'Practice Name', value: 'text', sortable: false },
      ],
    }
  },
}
</script>
