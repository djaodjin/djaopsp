<template>
  <fragment>
    <section-title :title="$t('improvement-plan.title')" />
    <tab-container :tabs="tabs" :lgCol="6">
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
        <tab-header :text="$t('improvement-plan.tab1.title')" />
        <div class="px-4 pt-sm-2 px-md-8">
          <p class="mb-2">{{ $t('improvement-plan.tab1.intro') }}</p>
          <form-improvement-plan
            :planPractices="planPractices"
            @practice:add="addPractice"
            @practice:remove="removePractice"
          />
        </div>
      </template>
      <template v-slot:tab2>
        <improvement-plan
          :header="$t('improvement-plan.tab2.title')"
          :planPractices="planPractices"
          :assessmentId="id"
          @practice:remove="removePractice"
        />
      </template>
    </tab-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import FormImprovementPlan from '@/components/FormImprovementPlan'
import ImprovementPlan from '@/components/ImprovementPlan'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'
import TabHeader from '@/components/TabHeader'

export default {
  name: 'AssessmentImprovementPlan',

  props: ['id'],

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
    ImprovementPlan,
    SectionTitle,
    TabContainer,
    TabHeader,
  },
}
</script>
