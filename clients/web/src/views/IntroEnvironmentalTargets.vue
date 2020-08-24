<template>
  <fragment>
    <intro-section
      :orgName="organization.name"
      :industryName="assessment.industry.name"
      title="Environmental Targets"
    >
      <div>
        <p>
          Define environmental targets for your organization and communicate its
          commitment to <b>adopt sustainable business practices</b>.
        </p>
        <p>
          Let environmental targets <b>guide and support your business</b> after
          benchmarking your performance data against other organizations in the
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
        <div class="text-center">
          <v-btn
            text
            class="mx-n4 mx-sm-0 mt-6"
            color="secondary"
            @click="advanceAssessment"
          >
            Continue without targets
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
  name: 'IntroEnvironmentalTargets',

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

    advanceAssessment() {
      // TODO: API call to update assessment status; then, redirect to assessment home
      console.log('Call API to advance assessment')
      this.$router.push({
        name: 'assessmentHome',
        params: { id: this.id },
      })
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
