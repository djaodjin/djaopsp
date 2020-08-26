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
        class="mt-8"
        :to="{
          name: 'assessmentPractices',
          params: { id, samplePath },
        }"
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

  props: ['org', 'id', 'samplePath'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const [organization, assessment] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
      ])
      this.organization = organization
      this.assessment = assessment
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
