<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <component
          :is="container"
          :class="[STANDALONE ? 'standalone' : 'embedded']"
          elevation="3"
        >
          <h1 class="pt-3 pb-2 pt-md-6 pb-md-3">{{ organization.name }}</h1>
          <v-row justify="center" justify-md="start">
            <v-col cols="12" md="6" xl="4">
              <section class="mb-4 px-md-4">
                <p>{{ $t('home.desc-assessment') }}</p>

                <div
                  v-if="
                    organization.assessments && organization.assessments.length
                  "
                >
                  <h3 class="mb-4">Active Sustainability Assessments</h3>
                  <ul
                    v-for="assessment in organization.assessments"
                    :key="assessment.key"
                  >
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
            <v-col cols="12" md="6" xl="4">
              <section class="mb-4 px-md-4">
                <p>{{ $t('home.desc-history') }}</p>
                <button-primary>{{ $t('home.btn-history') }}</button-primary>
              </section>
            </v-col>
            <!-- Comment out view best practices section
          <v-col cols="12" md="6" xl="4">
          <section class="mb-4 px-md-4">
            <p>{{ $t('home.desc-best-practices') }}</p>
            <button-primary>{{ $t('home.btn-best-practices') }}</button-primary>
          </section>
        </v-col> -->
          </v-row>
          <v-row>
            <v-col class="text-center text-md-right px-6 pt-5" cols="12">
              <span>Responding to a Sustainability Sourcing Event?</span>
              <a class="ml-1" href="#">Take the RFP and other RFx assessment</a>
            </v-col>
          </v-row>
        </component>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { VSheet } from 'vuetify/lib'
import ButtonPrimary from '@/components/ButtonPrimary'
import AssessmentInfo from '@/components/AssessmentInfo'

export default {
  name: 'Home',

  props: ['org'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const [organization] = await Promise.all([
        this.$context.getOrganization(this.org),
      ])
      this.organization = organization
    },
  },

  data() {
    return {
      organization: {},
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  computed: {
    container() {
      return this.STANDALONE ? 'div' : 'v-sheet'
    },
  },

  components: {
    AssessmentInfo,
    ButtonPrimary,
    VSheet,
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
.embedded {
  padding: 16px 20px;
}
</style>
