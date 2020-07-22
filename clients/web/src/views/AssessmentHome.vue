<template>
  <v-container v-if="assessment">
    <v-row>
      <v-col cols="12">
        <component
          :is="container"
          :class="[STANDALONE ? 'standalone' : 'embedded']"
          elevation="3"
        >
          <header-primary
            :linkText="organization.name"
            :linkTo="{ name: 'home' }"
            text="Environment Sustainability Assessment"
          />
          <v-row v-if="assessmentHasData" justify="center">
            <v-col cols="12" sm="8" md="6">
              <assessment-info :assessment="assessment" />
            </v-col>
            <v-col cols="12" sm="8" md="5">
              <assessment-stepper :assessment="assessment" />
            </v-col>
          </v-row>
        </component>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { VSheet } from 'vuetify/lib'
import { getOrganization } from '../mocks/organizations'
import { getAssessment } from '../mocks/assessments'
import AssessmentInfo from '@/components/AssessmentInfo'
import AssessmentStepper from '@/components/AssessmentStepper'
import HeaderPrimary from '@/components/HeaderPrimary'

export default {
  name: 'AssessmentHome',

  props: ['org', 'id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.organization = await getOrganization(this.org)
      this.assessment = await getAssessment(this.id)
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  computed: {
    container() {
      return this.STANDALONE ? 'div' : 'v-sheet'
    },
    assessmentHasData() {
      return Object.keys(this.assessment).length
    },
  },

  components: {
    VSheet,
    AssessmentInfo,
    AssessmentStepper,
    HeaderPrimary,
  },
}
</script>

<style lang="scss" scoped>
.embedded {
  max-width: 1185px;
  padding: 8px 16px 20px;
  margin: 0 auto;
}
</style>
