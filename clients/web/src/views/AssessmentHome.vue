<template>
  <v-container
    :class="[STANDALONE ? 'standalone' : 'embedded']"
    v-if="assessment"
  >
    <v-row>
      <v-col cols="12">
        <h1 class="my-2 my-md-6 assessment-title">
          Environment Sustainability Assessment
        </h1>
      </v-col>
    </v-row>
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6" lg="5">
        <assessment-info :assessment="assessment" />
      </v-col>
      <v-col cols="12" sm="8" md="5">
        <assessment-stepper :assessment="assessment" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
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

  components: {
    AssessmentInfo,
    AssessmentStepper,
  },
}
</script>

<style lang="scss" scoped>
.embedded h1 {
  color: white;
}
</style>
