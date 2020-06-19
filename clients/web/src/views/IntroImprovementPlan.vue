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
          <li>Your environmental targets</li>
          <li>Expert feedback</li>
          <li>Relevant business areas</li>
          <li>Other competitors in the industry</li>
        </ul>
        <button-primary
          class="mt-8"
          :to="{
            name: 'assessmentPlan',
            params: { id: $route.params.id },
          }"
          >Continue</button-primary
        >
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

  components: {
    Fragment,
    ButtonPrimary,
    IntroSection,
  },
}
</script>
