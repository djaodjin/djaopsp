<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="assessment.industryName"
      title="Scorecard"
    />
    <div v-if="loading">
      <loading-spinner />
    </div>
    <v-container v-else>
      <v-row>
        <v-col cols="12" sm="6" lg="4">
          <scorecard-scores :scores="topLevelScores"></scorecard-scores>
          <scorecard-business-areas
            :data="scoresByBusinessAreas"
          ></scorecard-business-areas>
        </v-col>
        <v-col>
          Targets go here!
        </v-col>
      </v-row>
      <button-primary
        class="mt-8"
        :to="{
          name: 'assessmentHome',
          params: { id },
        }"
      >
        Return to assessment
      </button-primary>
    </v-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import { getTopLevelScores, getScoresByBusinessAreas } from '../mocks/scorecard'
import ButtonPrimary from '@/components/ButtonPrimary'
import HeaderSecondary from '@/components/HeaderSecondary'
import LoadingSpinner from '@/components/LoadingSpinner'
import ScorecardScores from '@/components/ScorecardScores'
import ScorecardBusinessAreas from '@/components/ScorecardBusinessAreas'

export default {
  name: 'assessmentScorecard',

  props: ['org', 'id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.loading = true
      const [
        organization,
        assessment,
        topLevelScores,
        scoresByBusinessAreas,
      ] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
        getTopLevelScores(),
        getScoresByBusinessAreas(),
      ])

      this.organization = organization
      this.assessment = assessment
      this.topLevelScores = topLevelScores
      this.scoresByBusinessAreas = scoresByBusinessAreas
      this.loading = false
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
      loading: false,
      topLevelScores: null,
      scoresByBusinessAreas: [],
    }
  },

  components: {
    ButtonPrimary,
    Fragment,
    HeaderSecondary,
    LoadingSpinner,
    ScorecardScores,
    ScorecardBusinessAreas,
  },
}
</script>
