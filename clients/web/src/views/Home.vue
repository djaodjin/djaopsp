<template>
  <div>
    <h1>{{ organization.name }}</h1>

    <v-container>
      <v-row justify="center" justify-md="start">
        <v-col cols="11" md="6" xl="4">
          <section class="mb-4 px-md-4">
            <p>{{ $t('home.desc-assessment') }}</p>

            <div v-if="activeAssessments.length">
              <h3 class="mb-4">Active Sustainability Assessments</h3>
              <ul v-for="assessment in activeAssessments" :key="assessment.key">
                <assessment-info
                  class="mb-6"
                  :assessment="assessment"
                  :isClickable="true"
                />
              </ul>
            </div>

            <button-primary :to="{ name: 'newAssessment' }">{{
              $t('home.btn-assessment')
            }}</button-primary>
          </section>
        </v-col>
        <v-col cols="11" md="6" xl="4">
          <section class="mb-4 px-md-4">
            <p>{{ $t('home.desc-history') }}</p>
            <button-primary>{{ $t('home.btn-history') }}</button-primary>
          </section>
        </v-col>
        <v-col cols="11" md="6" xl="4">
          <section class="mb-4 px-md-4">
            <p>{{ $t('home.desc-best-practices') }}</p>
            <button-primary>{{ $t('home.btn-best-practices') }}</button-primary>
          </section>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import { getOrganization } from '../mocks/organizations'
import { getActiveAssessments } from '../mocks/assessments'
import ButtonPrimary from '@/components/ButtonPrimary'
import AssessmentInfo from '@/components/AssessmentInfo'

export default {
  name: 'Home',

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.organization = await getOrganization(this.$route.params.org)
      this.activeAssessments = await getActiveAssessments()
    },
  },

  data() {
    return {
      organization: { name: '' },
      activeAssessments: [],
    }
  },

  components: {
    AssessmentInfo,
    ButtonPrimary,
  },
}
</script>

<style lang="scss" scoped>
h3 {
  font-weight: 500;
  font-size: 1.2rem;
}
section {
  max-width: 600px;
  margin: 0 auto;
}
</style>
