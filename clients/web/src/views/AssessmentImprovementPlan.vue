<template>
  <fragment>
    <section-title :title="$t('improvement-plan.title')" />
    <tab-container :tabs="tabs">
      <template v-slot:tab2.title>
        <v-badge
          color="secondary"
          :content="planPractices.length"
          :value="planPractices.length"
        >
          {{ $t('improvement-plan.tab2.title') }}
        </v-badge>
      </template>
      <template v-slot:tab1>
        <div class="pa-4">
          <p class="mb-2">{{ $t('improvement-plan.tab1.intro') }}</p>
          <form-improvement-plan
            :planPractices="planPractices"
            @practice:add="addPractice"
            @practice:remove="removePractice"
          />
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

  methods: {
    addPractice(practice) {
      this.planPractices.push(practice)
    },
    removePractice(practice) {
      const removeIdx = this.planPractices.findIndex(
        (p) => p.id === practice.id
      )
      this.planPractices.splice(removeIdx, 1)
    },
  },

  data() {
    return {
      planPractices: [],
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
