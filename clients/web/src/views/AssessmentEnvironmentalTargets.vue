<template>
  <fragment>
    <section-title :title="$t('targets.title')" />
    <tab-container :tabs="tabs">
      <template v-slot:tab1>Market Situation Content!</template>
      <template v-slot:tab2>Environmental Targets Content!</template>
    </tab-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'

export default {
  name: 'AssessmentEnvironmentalTargets',

  data() {
    return {
      tabs: [
        { text: this.$t('targets.tab1-title'), href: 'tab-1' },
        { text: this.$t('targets.tab2-title'), href: 'tab-2' },
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
