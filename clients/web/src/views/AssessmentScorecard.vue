<template>
  <intro-section title="Scorecard">
    <div v-if="loading">
      <loading-spinner />
    </div>
    <div v-else>
      <scorecard-scores :scores="scores"></scorecard-scores>
      <button-primary
        class="mt-8"
        :to="{
          name: 'assessmentHome',
          params: { id: $route.params.id },
        }"
        >Return to assessment</button-primary
      >
    </div>
  </intro-section>
</template>

<script>
import { getScores } from '../mocks/scorecard'
import ButtonPrimary from '@/components/ButtonPrimary'
import IntroSection from '@/components/IntroSection'
import LoadingSpinner from '@/components/LoadingSpinner'
import ScorecardScores from '@/components/ScorecardScores'

export default {
  name: 'assessmentScorecard',

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.loading = true
      this.scores = await getScores()
      this.loading = false
    },
  },

  data() {
    return {
      loading: false,
      scores: null,
    }
  },

  components: {
    ButtonPrimary,
    IntroSection,
    LoadingSpinner,
    ScorecardScores,
  },
}
</script>
