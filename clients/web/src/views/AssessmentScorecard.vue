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
          <scorecard-business-areas :data="scoresByBusinessAreas" />
        </v-col>
        <v-col cols="12" sm="6" lg="8">
          <scorecard-targets :targets="targets" />
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
import {
  getTopLevelScores,
  getScoresByBusinessAreas,
  getTargets,
} from '../mocks/scorecard'
import ButtonPrimary from '@/components/ButtonPrimary'
import HeaderSecondary from '@/components/HeaderSecondary'
import LoadingSpinner from '@/components/LoadingSpinner'
import ScorecardScores from '@/components/ScorecardScores'
import ScorecardBusinessAreas from '@/components/ScorecardBusinessAreas'
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
      ] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
        getTopLevelScores(),
        getScoresByBusinessAreas(),
        getTargets(),
      ])

      this.organization = organization
      this.assessment = assessment
      this.topLevelScores = topLevelScores
      this.scoresByBusinessAreas = scoresByBusinessAreas
      this.targets = targets
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
    ScorecardTargets,
  },
}
</script>
