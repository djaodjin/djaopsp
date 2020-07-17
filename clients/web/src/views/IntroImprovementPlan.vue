<template>
  <fragment>
    <intro-section title="Improvement Plan">
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
          <li class="mb-1">&mdash; Other competitors in the industry</li>
        </ul>
        <button-primary
          class="mt-8"
          :to="{
            name: 'assessmentPlan',
            params: { id, samplePath },
          }"
          >Continue</button-primary
        >
        <div class="text-center">
          <v-btn text class="mt-6" color="secondary" @click="advanceAssessment">
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
  name: 'IntroCurrentPractices',

  props: ['id', 'samplePath'],

  methods: {
    advanceAssessment() {
      // TODO: API call to update assessment status; then, redirect to assessment home
      console.log('Call API to advance assessment')
      this.$router.push({
        name: 'assessmentHome',
        params: { id: this.$route.params.id },
      })
    },
  },

  components: {
    Fragment,
    ButtonPrimary,
    IntroSection,
  },
}
</script>
