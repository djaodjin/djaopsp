<template>
  <div class="pa-8" v-if="!planPractices.length">
    <p class="text-h5 text-center">Your improvement plan is empty!</p>
    <p class="text-subtitle-1 text-center">
      Create an improvement plan by searching and selecting opportunities that
      align with your environmental targets or support specific areas of your
      business.
    </p>
  </div>
  <div v-else>
    <tab-header :text="header" />
    <div class="pa-4 pt-sm-2 px-md-8">
      <h3 class="mb-2">Support your business areas</h3>
      <ol class="pl-0">
        <v-container
          tag="li"
          class="pa-0"
          v-for="practice in planPractices"
          :key="practice.id"
        >
          <v-row>
            <v-col cols="12">
              <practice-overview
                :practice="practice"
                :valueCategory="defaultCategory"
              />
              <button-secondary
                class="mt-3 mb-2"
                color="red"
                @click="$emit('practice:remove', practice)"
                >Remove From Plan</button-secondary
              >
            </v-col>
          </v-row>
        </v-container>
      </ol>
      <chart-practice-values-aggregate
        class="aggregate-chart my-4 mt-md-8 mt-xl-10 mx-xl-12"
        :practices="planPractices"
      />
      <button-primary class="mb-5" @click="saveImprovementPlan"
        >Save Improvement Plan</button-primary
      >
    </div>
  </div>
</template>

<script>
import { PRACTICE_VALUE_CATEGORY_DEFAULT } from '@/config/app'
import ButtonPrimary from '@/components/ButtonPrimary'
import ButtonSecondary from '@/components/ButtonSecondary'
import ChartPracticeValuesAggregate from '@/components/ChartPracticeValuesAggregate'
import PracticeOverview from '@/components/PracticeOverview'
import TabHeader from '@/components/TabHeader'

export default {
  name: 'ImprovementPlan',

  props: ['assessmentId', 'header', 'planPractices'],

  data() {
    return {
      defaultCategory: PRACTICE_VALUE_CATEGORY_DEFAULT,
    }
  },

  methods: {
    saveImprovementPlan() {
      // TODO: API call to update assessment status; then, redirect to assessment home
      console.log('Call API to advance assessment')
      this.$router.push({
        name: 'assessmentHome',
        params: { id: this.assessmentId },
      })
    },
  },

  components: {
    ButtonPrimary,
    ButtonSecondary,
    ChartPracticeValuesAggregate,
    PracticeOverview,
    TabHeader,
  },
}
</script>

<style lang="scss" scoped>
ol {
  list-style: none;
}
</style>
