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
        <v-col cols="12" sm="6" lg="4" xl="4">
          <scorecard-scores :scores="topLevelScores"></scorecard-scores>
          <scorecard-business-areas :data="scoresByBusinessAreas" />
          <scorecard-targets :targets="targets" />
        </v-col>
        <v-col cols="12" sm="6" lg="8" xl="8">
          <scorecard-practices :practices="improvementPlanPractices" />
          <scorecard-practices-chart :practices="improvementPlanPractices" />
          <button-primary
            class="mt-6"
            :to="{
              name: 'assessmentHome',
              params: { id },
            }"
          >
            Return to assessment
          </button-primary>
        </v-col>
      </v-row>
    </v-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import { getResults } from '../mocks/ip-results'
import { getTopLevelScores, getScoresByBusinessAreas } from '../mocks/scorecard'
import { getAssessmentTargets } from '../mocks/assessments'

import ButtonPrimary from '@/components/ButtonPrimary'
import HeaderSecondary from '@/components/HeaderSecondary'
import LoadingSpinner from '@/components/LoadingSpinner'
import ScorecardScores from '@/components/ScorecardScores'
import ScorecardBusinessAreas from '@/components/ScorecardBusinessAreas'
import ScorecardPractices from '@/components/ScorecardPractices'
import ScorecardPracticesChart from '@/components/ScorecardPracticesChart'
import ScorecardTargets from '@/components/ScorecardTargets'

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
        targets,
        improvementPlanPractices,
      ] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
        getTopLevelScores(),
        getScoresByBusinessAreas(),
        getAssessmentTargets(), // TODO: Remove this as this should be part of the assessment
        getResults(),
      ])

      this.organization = organization
      this.assessment = assessment
      this.topLevelScores = topLevelScores
      this.scoresByBusinessAreas = scoresByBusinessAreas
      this.targets = targets
      this.improvementPlanPractices = improvementPlanPractices
      this.loading = false
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
      improvementPlanPractices: [],
      loading: false,
      topLevelScores: null,
      scoresByBusinessAreas: [],
      targets: [],
    }
  },

  components: {
    ButtonPrimary,
    Fragment,
    HeaderSecondary,
    LoadingSpinner,
    ScorecardScores,
    ScorecardBusinessAreas,
    ScorecardPractices,
    ScorecardTargets,
    ScorecardPracticesChart,
  },
}
</script>
