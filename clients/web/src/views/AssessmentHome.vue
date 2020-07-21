<template>
  <v-container v-if="assessment">
    <v-row>
      <v-col cols="12">
        <component
          :is="container"
          :class="[STANDALONE ? 'standalone' : 'embedded']"
          elevation="3"
        >
          <v-row>
            <v-col>
              <h1 class="my-2 my-md-6 assessment-title">
                Environment Sustainability Assessment
              </h1>
            </v-col>
          </v-row>
          <v-row justify="center">
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
import { getAssessment } from '../mocks/assessments'
import AssessmentInfo from '@/components/AssessmentInfo'
import AssessmentStepper from '@/components/AssessmentStepper'

export default {
  name: 'AssessmentHome',

  props: ['id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.assessment = await getAssessment(this.id)
    },
  },

  data() {
    return {
      assessment: null,
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  computed: {
    container() {
      return this.STANDALONE ? 'div' : 'v-sheet'
    },
  },

  components: {
    VSheet,
    AssessmentInfo,
    AssessmentStepper,
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
