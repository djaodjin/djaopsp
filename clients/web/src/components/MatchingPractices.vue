<template>
  <div class="text-center pb-6" v-if="practices.length">
    <h3 class="mb-1 text-h6">Matching Practices: {{ practices.length }}</h3>
    <p>Select practices to add to your improvement plan</p>
    <v-data-table
      class="matching-practices"
      :headers="headers"
      :items="practices"
      :sort-by="[valueKey, 'implementationRate']"
      :sort-desc="[true, false]"
      multi-sort
      must-sort
      disable-pagination
      disable-filtering
      hide-default-footer
    >
      <template v-slot:item="{ item, isMobile }">
        <v-container v-if="isMobile" class="pt-2">
          <v-row>
            <v-col cols="4">
              <div>
                <practice-value-chip dark :value="item[valueKey]" />
                <br />
                <v-subheader>{{ practiceValue.text }}</v-subheader>
              </div>
              <div class="mt-2">
                <implementation-value-chip :value="item.implementationRate" />
                <br />
                <v-subheader>
                  Competitors implementing this practice
                </v-subheader>
              </div>
            </v-col>
            <v-col class="text-left" cols="8">
              <practice-section-header
                :small="true"
                :section="item.question.section.name"
                :subcategory="item.question.subcategory.name"
              />
              <p class="description">{{ item.question.text }}</p>
              <button-primary
                v-if="planPractices.findIndex((p) => p.id === item.id) === -1"
                @click="$emit('practice:add', item)"
              >
                Add To Plan
              </button-primary>
              <button-secondary
                color="red"
                v-else
                @click="$emit('practice:remove', item)"
              >
                Remove From Plan
              </button-secondary>
            </v-col>
          </v-row>
        </v-container>
        <tr v-else>
          <td>
            <practice-value-chip dark :value="item[valueKey]" />
          </td>
          <td>
            <implementation-value-chip :value="item.implementationRate" />
          </td>
          <td class="py-4">
            <practice-section-header
              :small="true"
              :section="item.question.section.name"
              :subcategory="item.question.subcategory.name"
            />
            <p class="description text-left">{{ item.question.text }}</p>
            <button-primary
              v-if="planPractices.findIndex((p) => p.id === item.id) === -1"
              @click="$emit('practice:add', item)"
            >
              Add To Plan
            </button-primary>
            <button-secondary
              color="red"
              v-else
              @click="$emit('practice:remove', item)"
            >
              Remove From Plan
            </button-secondary>
          </td>
        </tr>
      </template>
    </v-data-table>
  </div>
  <div class="text-center pb-4" v-else>
    <h3 class="mb-1 text-h6">No Results Found</h3>
    <p>Change the search filters and try again</p>
  </div>
</template>

<script>
import { PRACTICE_VALUE_CATEGORIES } from '../config'
import ButtonPrimary from '@/components/ButtonPrimary'
import ButtonSecondary from '@/components/ButtonSecondary'
import PracticeSectionHeader from '@/components/PracticeSectionHeader'
import PracticeValueChip from '@/components/PracticeValueChip'
import ImplementationValueChip from '@/components/ImplementationValueChip'

export default {
  name: 'MatchingPractices',

  props: ['planPractices', 'practices', 'valueKey'],

  computed: {
    practiceValue() {
      return PRACTICE_VALUE_CATEGORIES.find((c) => c.value === this.valueKey)
    },
    headers() {
      return [
        {
          text: this.practiceValue.text,
          align: 'start',
          value: this.practiceValue.value,
          filterable: false,
        },
        {
          text: 'Implementation Rate',
          value: 'implementationRate',
          filterable: false,
        },
        {
          text: 'Practice Name',
          value: 'text',
          sortable: false,
          filterable: false,
        },
      ]
    },
  },

  components: {
    ButtonPrimary,
    ButtonSecondary,
    PracticeValueChip,
    PracticeSectionHeader,
    ImplementationValueChip,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.matching-practices {
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
}
</style>
