<template>
  <fragment>
    <intro-section
      :orgName="organization.name"
      :industryName="assessment.industryName"
      title="Improvement Plan"
    >
      <div>
        <p>
          Create an improvement plan to help your organization
          <b>focus on implementing or improving business practices</b> that will
          yield the most value for the organization in terms of
          <b>environmental impact and competitive benefits</b>.
        </p>
        <p>Identify and prioritize opportunities for improvement based on:</p>
        <ul>
          <li class="mb-1">&mdash; Your environmental targets</li>
          <li class="mb-1">&mdash; Expert feedback</li>
          <li class="mb-1">&mdash; Relevant business areas</li>
          <li class="mb-1">&mdash; Other organizations in the industry</li>
        </ul>
        <button-primary
          class="mt-8"
          :to="{
            name: 'assessmentPlan',
            params: { id },
          }"
          >Continue</button-primary
        >
        <div class="text-center">
          <v-btn
            text
            class="mx-n4 mx-sm-0 mt-6"
            color="secondary"
            :to="{
              name: 'assessmentHome',
              params: { org, slug },
            }"
          >
            Continue without Improvement Plan
          </v-btn>
        </div>
      </div>
    </intro-section>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import ButtonPrimary from '@/components/ButtonPrimary'
import IntroSection from '@/components/IntroSection'

export default {
  name: 'IntroImprovementPlan',

  props: ['org', 'id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const [organization, assessment] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.org, this.id),
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
    Fragment,
    ButtonPrimary,
    IntroSection,
  },
}
</script>
