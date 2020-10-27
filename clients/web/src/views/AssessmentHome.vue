<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <component
          :is="container"
          :class="[STANDALONE ? 'standalone' : 'embedded']"
          elevation="3"
        >
          <header-primary
            :linkText="organization.name"
            :linkTo="{ name: 'home', params: { org: $route.params.org } }"
            text="Environment Sustainability Assessment"
          />
          <v-row v-if="assessment" justify="center">
            <v-col cols="12" sm="8" md="6">
              <assessment-info :organizationId="org" :assessment="assessment" />
            </v-col>
            <v-col cols="12" sm="8" md="5">
              <assessment-stepper
                :organization="organization"
                :assessment="assessment"
              />
            </v-col>
          </v-row>
        </component>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { VSheet } from 'vuetify/lib'
import AssessmentInfo from '@/components/AssessmentInfo'
import AssessmentStepper from '@/components/AssessmentStepper'
import FormSelectIndustry from '@/components/FormSelectIndustry'
import HeaderPrimary from '@/components/HeaderPrimary'

export default {
  name: 'AssessmentHome',

  props: ['org', 'slug'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const industryPath = `/${this.$route.params.pathMatch}/`
      this.organization = await this.$context.getOrganization(this.org)
      this.assessment = await this.$context.getAssessment(
        this.organization,
        this.slug,
        industryPath
      )
    },
  },

  data() {
    return {
      organization: {},
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
    FormSelectIndustry,
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
