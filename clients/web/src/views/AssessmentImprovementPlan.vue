<template>
  <fragment>
    <section-title title="Improvement Plan" />
    <tab-container :tabs="tabs">
      <template v-slot:tab1>
        <div class="pa-4">
          <p>{{ $t('targets.tab1.intro') }}</p>
        </div>
      </template>
      <template v-slot:tab2>
        <div class="pa-4">
          <p>{{ $t('targets.tab2.intro') }}</p>
        </div>
      </template>
    </tab-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'

export default {
  name: 'AssessmentImprovementPlan',

  data() {
    return {
      tabs: [
        { text: this.$t('targets.tab1.title'), href: 'tab-1' },
        { text: this.$t('targets.tab2.title'), href: 'tab-2' },
      ],
      tab: null,
    }
  },

  components: {
    Fragment,
    SectionTitle,
    TabContainer,
  },
}
</script>
