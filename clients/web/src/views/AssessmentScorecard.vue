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
import { getOrganization } from '../mocks/organizations'
import { getAssessment } from '../mocks/assessments'
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
      this.organization = await getOrganization(this.org)
      this.assessment = await getAssessment(this.id)
      this.topLevelScores = await getTopLevelScores()
      this.scoresByBusinessAreas = await getScoresByBusinessAreas()
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
