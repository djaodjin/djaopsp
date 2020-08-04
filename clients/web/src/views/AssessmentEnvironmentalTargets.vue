<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="assessment.industryName"
      :title="$t('targets.title')"
    />
    <tab-container :tabs="tabs" :mdCol="6" :lgCol="6">
      <template v-slot:tab1>
        <tab-header :text="$t('targets.tab1.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <p>{{ $t('targets.tab1.intro') }}</p>
          <business-comparison />
        </div>
      </template>
      <template v-slot:tab2>
        <tab-header :text="$t('targets.tab2.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <p>{{ $t('targets.tab2.intro') }}</p>
          <form-environmental-targets :assessmentId="id" />
        </div>
      </template>
    </tab-container>
    <dialog-confirm
      storageKey="previousTargets"
      :checkStateAsync="checkPreviousTargets"
      title="Previous Targets"
      actionText="Ok, thanks"
    >
      <p>
        Your organization has submitted environmental targets in the past for
        the industry segment selected.
      </p>
      <p>
        Please edit or re-submit the targets from the most recent assessment.
      </p>
    </dialog-confirm>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import BusinessComparison from '@/components/BusinessComparison'
import DialogConfirm from '@/components/DialogConfirm'
import FormEnvironmentalTargets from '@/components/FormEnvironmentalTargets'
import HeaderSecondary from '@/components/HeaderSecondary'
import TabContainer from '@/components/TabContainer'
import TabHeader from '@/components/TabHeader'

export default {
  name: 'AssessmentEnvironmentalTargets',

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
    async checkPreviousTargets() {
      // TODO: Send request to check if previous targets have been submitted
      return new Promise((resolve) => {
        console.log('Check if previous targets have been submitted')
        resolve(true)
      })
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
      tabs: [
        { text: this.$t('targets.tab1.title'), href: 'tab-1' },
        { text: this.$t('targets.tab2.title'), href: 'tab-2' },
      ],
      tab: null,
    }
  },

  components: {
    BusinessComparison,
    DialogConfirm,
    FormEnvironmentalTargets,
    Fragment,
    HeaderSecondary,
    TabContainer,
    TabHeader,
  },
}
</script>
