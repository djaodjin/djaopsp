<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="asssessment.industryName"
      title="Scorecard"
    />
    <div v-if="loading">
      <loading-spinner />
    </div>
    <v-container v-else>
      <v-row>
        <v-col cols="12" sm="6" lg="4" xl="4">
          <scorecard-scores :scores="assessmentScore"></scorecard-scores>
          <scorecard-business-areas :benchmarks="assessmentScore.benchmarks" />
          <scorecard-targets :targets="assessment.targets" />
        </v-col>
        <v-col cols="12" sm="6" lg="8" xl="8">
          <scorecard-practices :practices="assessment.improvementPlan" />
          <scorecard-practices-chart :practices="assessment.improvementPlan" />
          <button-primary
            class="mt-6"
            :to="
              $routeMap.get('assessmentHome').getPath({
                org: organization.id,
                slug: assessment.slug,
                industryPath: assessment.industryPath,
              })
            "
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
import API from '@/common/api'

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
      const [organization, assessment, score] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.org, this.id),
        API.getBenchmarks(),
      ])

      this.organization = organization
      this.assessment = assessment
      this.assessmentScore = score
      this.loading = false
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
      assessmentScore: {},
      loading: false,
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
