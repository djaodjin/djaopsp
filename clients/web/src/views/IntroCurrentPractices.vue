<template>
  <fragment>
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
        <ButtonPrimary class="mt-8">Continue</ButtonPrimary>
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
