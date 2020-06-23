<template>
  <fragment>
    <section-title :title="$t('targets.title')" />
    <tab-container :tabs="tabs">
      <template v-slot:tab1>
        <div class="pa-4">
          <p>{{ $t('targets.tab1.intro') }}</p>
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-management.png"
          />
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-construction.png"
          />
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-eng-and-design.png"
          />
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-office-grounds.png"
          />
          <img
            class="d-block mx-auto mb-6"
            alt
            src="../assets/images/chart-procurement.png"
          />
        </div>
      </template>
      <template v-slot:tab2>
        <div class="pa-4">
          <p>{{ $t('targets.tab2.intro') }}</p>
          <form-environmental-targets />
        </div>
      </template>
    </tab-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import FormEnvironmentalTargets from '@/components/FormEnvironmentalTargets'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'

export default {
  name: 'AssessmentEnvironmentalTargets',

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
    FormEnvironmentalTargets,
    Fragment,
    SectionTitle,
    TabContainer,
  },
}
</script>
