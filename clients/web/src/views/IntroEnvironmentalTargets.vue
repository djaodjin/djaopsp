<template>
  <fragment>
    <intro-section
      :orgName="organization.name"
      :industryName="assessment.industryName"
      title="Environmental Targets"
    >
      <div>
        <p>
          Define environmental targets for your organization and communicate its
          commitment to <b>adopt sustainable business practices</b>.
        </p>
        <p>
          Let environmental targets <b>guide and support your business</b> after
          benchmarking your performance data against other competitors in the
          industry.
        </p>
        <button-primary
          class="mt-8"
          :to="{
            name: 'assessmentTargets',
            params: { id, samplePath },
          }"
          >Continue</button-primary
        >
      </div>
    </intro-section>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import { getOrganization } from '../mocks/organizations'
import { getAssessment } from '../mocks/assessments'
import ButtonPrimary from '@/components/ButtonPrimary'
import IntroSection from '@/components/IntroSection'

export default {
  name: 'IntroEnvironmentalTargets',

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
    Fragment,
    ButtonPrimary,
    IntroSection,
  },
}
</script>
