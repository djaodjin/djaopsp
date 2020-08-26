<template>
  <intro-section
    :orgName="organization.name"
    :industryName="assessment.industryName"
    title="Current Practices"
  >
    <div>
      <p>
        Please respond to a list of questions related to the current practices
        of your organization. Responses must be accurate and verifiable.
      </p>
      <p>
        Every question answered is automatically saved so you can exit and
        resume this questionnaire at any time.
      </p>
      <form @submit.prevent="setIndustry">
        <label data-cy="industry-label" for="industry" class="d-block mb-3">
          Before you start, please choose the industry that best applies to your
          organization:
        </label>
        <v-select
          id="industry"
          hide-details
          label="Industry segment"
          class="mb-6"
          :items="industries"
        >
          <template v-slot:item="{ item, on, attrs }">
            <v-list-item-content v-bind="attrs" v-on="on">
              <v-list-item-title
                :class="[item.isChild ? 'child' : 'single']"
                v-text="item.text"
                @click="selectIndustry(item)"
              ></v-list-item-title>
            </v-list-item-content>
          </template>
        </v-select>
        <div v-show="industry" class="text-right">
          <button-primary type="submit" display="inline">Next</button-primary>
        </div>
        <div class="text-right mt-8 mb-4">
          <span>Don't know what to select?</span>
          <a data-cy="examples" class="ml-2" href="/docs/faq/#general-4"
            >See examples.</a
          >
        </div>
      </form>
    </div>
  </intro-section>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'
import IntroSection from '@/components/IntroSection'

export default {
  name: 'IntroCurrentPractices',

  props: ['org', 'id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const [organization, assessment, industries] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.org, this.id),
        this.$context.getIndustries(),
      ])
      this.organization = organization
      this.assessment = assessment
      this.industries = industries
    },
    selectIndustry(item) {
      this.industry = {
        title: item.text,
        path: item.value,
      }
    },
    setIndustry() {
      this.$context.setAssessmentIndustry(this.id, this.industry)
      // Slashes (in the sample path) are not encoded when they are included in the path
      // But they are if they are passed as a param
      // Per: https://github.com/vuejs/vue-router/issues/787
      this.$router.push(
        `/${this.org}/assess/${this.id}/content/${this.industry.path}/`
      )
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
      industries: [],
      industry: null,
    }
  },

  components: {
    ButtonPrimary,
    IntroSection,
  },
}
</script>

<style lang="scss" scoped>
.v-list-item__title.child {
  margin-left: 16px;
}
</style>
