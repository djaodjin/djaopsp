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
      <button-primary
        data-cy="btn-continue"
        class="mt-8"
        :to="`/${this.org}/assess/${this.slug}${this.assessment.industryPath}`"
        >Continue</button-primary
      >
    </div>
  </intro-section>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'
import IntroSection from '@/components/IntroSection'
export default {
  name: 'IntroCurrentPractices',

  props: ['org', 'slug'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const industryPath = this.$route.params.pathMatch
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
      assessment: {},
    }
  },

  components: {
    ButtonPrimary,
    IntroSection,
  },
}
</script>
