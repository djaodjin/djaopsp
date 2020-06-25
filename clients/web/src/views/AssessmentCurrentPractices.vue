<template>
  <fragment>
    <section-title title="Current Practices" />
    <tab-container :tabs="tabs">
      <template v-slot:tab1>
        <div class="pa-4">
          <assessment-sections />
        </div>
      </template>
      <template v-slot:tab2>
        <div class="pa-4">
          <p>{{ $t('practices.tab2.intro') }}</p>
        </div>
      </template>
    </tab-container>
    <practices-progress-indicator questions="48" answers="46" />
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import PracticesProgressIndicator from '@/components/PracticesProgressIndicator'
import AssessmentSections from '@/components/AssessmentSections'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'

export default {
  name: 'AssessmentCurrentPractices',

  data() {
    return {
      tabs: [
        { text: this.$t('practices.tab1.title'), href: 'tab-1' },
        { text: this.$t('practices.tab2.title'), href: 'tab-2' },
      ],
    }
  },

  components: {
    Fragment,
    PracticesProgressIndicator,
    AssessmentSections,
    SectionTitle,
    TabContainer,
  },
}
</script>
