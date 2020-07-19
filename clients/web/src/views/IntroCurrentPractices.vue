<template>
  <intro-section title="Current Practices">
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
import ButtonPrimary from '@/components/ButtonPrimary'
import IntroSection from '@/components/IntroSection'

export default {
  name: 'IntroCurrentPractices',

  props: ['id', 'samplePath'],

  components: {
    ButtonPrimary,
    IntroSection,
  },
}
</script>
