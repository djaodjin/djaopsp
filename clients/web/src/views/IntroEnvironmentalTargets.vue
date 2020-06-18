<template>
  <fragment>
    <intro-section title="Environmental Targets">
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
  name: 'IntroEnvironmentalTargets',

  components: {
    Fragment,
    ButtonPrimary,
    IntroSection,
  },
}
</script>
