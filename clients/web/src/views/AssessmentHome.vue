<template>
  <div class="assessment-container">
    <h1 class="assessment-title">Environment Sustainability Assessment</h1>
    <v-container>
      <v-row justify="center">
        <v-col cols="12" md="8" lg="6">
          <assessment-info />
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import AssessmentInfo from '@/components/AssessmentInfo'

export default {
  name: 'AssessmentHome',

  data: () => ({}),

  components: {
    AssessmentInfo,
  },
}
</script>
