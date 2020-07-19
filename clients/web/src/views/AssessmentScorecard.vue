<template>
  <intro-section title="Scorecard" :cols="12">
    <div v-if="loading">
      <loading-spinner />
    </div>
    <div v-else>
      <scorecard-scores :scores="topLevelScores"></scorecard-scores>
      <scorecard-business-areas
        :data="scoresByBusinessAreas"
      ></scorecard-business-areas>
      <button-primary
        class="mt-8"
        :to="{
          name: 'assessmentHome',
          params: { id },
        }"
        >Return to assessment</button-primary
      >
    </div>
  </intro-section>
</template>

<script>
import { getTopLevelScores, getScoresByBusinessAreas } from '../mocks/scorecard'
import ButtonPrimary from '@/components/ButtonPrimary'
import IntroSection from '@/components/IntroSection'
import LoadingSpinner from '@/components/LoadingSpinner'
import ScorecardScores from '@/components/ScorecardScores'
import ScorecardBusinessAreas from '@/components/ScorecardBusinessAreas'

export default {
  name: 'assessmentScorecard',

  props: ['id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.loading = true
      this.topLevelScores = await getTopLevelScores()
      this.scoresByBusinessAreas = await getScoresByBusinessAreas()
      this.loading = false
    },
  },

  data() {
    return {
      loading: false,
      topLevelScores: null,
      scoresByBusinessAreas: [],
    }
  },

  components: {
    ButtonPrimary,
    IntroSection,
    LoadingSpinner,
    ScorecardScores,
    ScorecardBusinessAreas,
  },
}
</script>
