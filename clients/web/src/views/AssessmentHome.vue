<template>
  <div class="assessment-container">
    <h1 class="assessment-title">Environment Sustainability Assessment</h1>
    <v-container v-if="assessment">
      <v-row justify="center">
        <v-col cols="12" sm="8" md="6" lg="5">
          <assessment-info :assessment="assessment" />
        </v-col>
        <v-col cols="12" sm="8" md="5">
          <assessment-stepper :assessment="assessment" />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import { getAssessment } from '../mocks/assessments'
import AssessmentInfo from '@/components/AssessmentInfo'
import AssessmentStepper from '@/components/AssessmentStepper'

export default {
  name: 'AssessmentHome',

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.assessment = await getAssessment(this.$route.params.id)
    },
  },

  data() {
    return {
      assessment: null,
    }
  },

  components: {
    AssessmentInfo,
    AssessmentStepper,
  },
}
</script>
