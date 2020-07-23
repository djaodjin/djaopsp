<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="assessment.industryName"
      :title="$t('improvement-plan.title')"
    />
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
import HeaderSecondary from '@/components/HeaderSecondary'
import ImprovementPlan from '@/components/ImprovementPlan'
import TabContainer from '@/components/TabContainer'
import TabHeader from '@/components/TabHeader'

export default {
  name: 'AssessmentImprovementPlan',

  props: ['org', 'id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const [organization, assessment] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
      ])
      this.organization = organization
      this.assessment = assessment
    },
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
      organization: {},
      assessment: {},
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
    HeaderSecondary,
    TabContainer,
    TabHeader,
  },
}
</script>
