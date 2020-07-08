<template>
  <fragment>
    <section-title :title="$t('improvement-plan.title')" />
    <tab-container :tabs="tabs">
      <template v-slot:tab1>
        <div class="pa-4">
          <p class="mb-2">{{ $t('improvement-plan.tab1.intro') }}</p>
          <form-improvement-plan />
        </div>
      </template>
      <template v-slot:tab2>
        <div class="pa-4">
          <p>TBD</p>
        </div>
      </template>
    </tab-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import FormImprovementPlan from '@/components/FormImprovementPlan'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'

export default {
  name: 'AssessmentImprovementPlan',

  data() {
    return {
      tabs: [
        { text: this.$t('improvement-plan.tab1.title'), href: 'tab-1' },
        { text: this.$t('improvement-plan.tab2.title'), href: 'tab-2' },
      ],
      tab: null,
    }
  },

  components: {
    Fragment,
    FormImprovementPlan,
    SectionTitle,
    TabContainer,
  },
}
</script>
