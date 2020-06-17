<template>
  <div class="assessment-container">
    <h1 class="assessment-title">Environment Sustainability Assessment</h1>
    <v-container>
      <v-row justify="center">
        <v-col cols="11" sm="8" md="6" lg="5">
          <assessment-info />
        </v-col>
        <v-col cols="11" sm="8" md="5" lg="4">
          <assessment-stepper />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import AssessmentInfo from '@/components/AssessmentInfo'
import AssessmentStepper from '@/components/AssessmentStepper'

export default {
  name: 'AssessmentHome',

  data: () => ({}),

  components: {
    AssessmentInfo,
    AssessmentStepper,
  },
}
</script>
