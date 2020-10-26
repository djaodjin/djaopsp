<template>
  <v-container>
    <v-row>
      <v-col cols="12" v-if="organization">
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
          <v-row justify="center">
            <v-col cols="12" sm="8" md="5">
              <form-select-industry
                :organization="organization"
                @industry:set="createAssessment"
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
import API from '@/common/api'
import FormSelectIndustry from '@/components/FormSelectIndustry'
import HeaderPrimary from '@/components/HeaderPrimary'

export default {
  name: 'AssessmentCreate',

  props: ['org'],

  created() {
    this.fetchData()
  },

  methods: {
    createAssessment(industry) {
      API.createAssessment(this.organization, { campaign: 'assessment' }).then(
        async (assessment) => {
          const newAssessment = await API.setAssessmentIndustry(
            this.organization,
            assessment,
            industry
          )
          this.organization.addAssessment(newAssessment)
          this.$router.push(
            `/${this.org}/home/${newAssessment.slug}/${industry.path}/`
          )
        }
      )
    },
    async fetchData() {
      this.organization = await this.$context.getOrganization(this.org)
    },
  },

  data() {
    return {
      organization: null,
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
