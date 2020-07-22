<template>
  <intro-section
    :orgName="organization.name"
    :industryName="assessment.industryName"
    title="Current Practices"
  >
    <div>
      <p>
        Please respond to a list of questions related to the current practices
        of your organization.
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
import { getOrganization } from '../mocks/organizations'
import { getAssessment } from '../mocks/assessments'
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
      this.organization = await getOrganization(this.org)
      this.assessment = await getAssessment(this.id)
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
