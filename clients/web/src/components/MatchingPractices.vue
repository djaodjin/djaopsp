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
    >
      <template v-slot:item="{ item }">
        <v-container class="pt-2">
          <v-row>
            <v-col cols="4">
              <div>
                <practice-value-chip dark :value="item.value" />
                <br />
                <v-subheader>Practice Value</v-subheader>
              </div>
              <div class="mt-2">
                <implementation-value-chip :value="item.implementation" />
                <br />
                <v-subheader>
                  Competitors implementing this practice
                </v-subheader>
              </div>
            </v-col>
            <v-col class="text-left" cols="8">
              <template v-if="item.section && item.subcategory">
                <practice-section-header
                  :small="true"
                  :section="item.section.name"
                  :subcategory="item.subcategory.name"
                />
              </template>
              <p class="description">{{ item.text }}</p>
              <button-secondary @click="addPractice(item.id)">
                Remove From Plan
              </button-secondary>
            </v-col>
          </v-row>
        </v-container>
      </template>
    </v-data-table>
  </div>
  <div class="text-center" v-else>
    <h3 class="mb-1 text-h6">No Results Found</h3>
    <p>Change the search filters and try again</p>
  </div>
</template>

<script>
import ButtonSecondary from '@/components/ButtonSecondary'
import PracticeSectionHeader from '@/components/PracticeSectionHeader'
import PracticeValueChip from '@/components/PracticeValueChip'
import ImplementationValueChip from '@/components/ImplementationValueChip'

export default {
  name: 'MatchingPractices',

  props: ['results'],

  methods: {
    addPractice(id) {
      console.log(`Add practice ${id} to improvement plan`)
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

  components: {
    PracticeValueChip,
    PracticeSectionHeader,
    ImplementationValueChip,
    ButtonSecondary,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.results {
  & ::v-deep tbody > div:nth-child(even) {
    background-color: #f8f8f8;
  }
  .v-subheader {
    padding: 4px 0;
    height: auto;
    display: block;
  }
  .description {
    font-size: 0.9rem;
  }
  /* .subcategory {
    display: block;
    font-weight: 600;
    margin-top: 2px;
    margin-bottom: 5px;
  }
  .text-caption {
    display: block;
    line-height: 1;
  } */
}
</style>
