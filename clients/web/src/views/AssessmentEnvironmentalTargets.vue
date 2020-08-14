<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="assessment.industryName"
      :title="$t('targets.title')"
    />
    <tab-container
      :tabs="tabs"
      :mdCol="6"
      :lgCol="6"
      :xlLeftCol="8"
      :xlRightCol="4"
    >
      <template v-slot:tab1>
        <tab-header :text="$t('targets.tab1.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <p class="mb-0">{{ $t('targets.tab1.intro') }}</p>
          <form-environmental-targets :assessment="assessment" />
        </div>
      </template>
      <template v-slot:tab2>
        <tab-header :text="$t('targets.tab2.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <p>
            {{
              $t('targets.tab2.intro', {
                industryName: assessment.industryName,
              })
            }}
          </p>
          <ul v-for="(benchmark, index) in score.benchmarks" :key="index">
            <chart-practices-implementation
              :section="benchmark.section"
              :scores="benchmark.scores"
              :companyScore="benchmark.companyScore"
            />
          </ul>
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
import { getScore } from '@/common/api'
import ChartPracticesImplementation from '@/components/ChartPracticesImplementation'
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
      const [organization, assessment, score] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
        getScore(this.org, this.id),
      ])
      this.organization = organization
      this.assessment = assessment
      this.score = score
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
      score: {},
      tabs: [
        { text: this.$t('targets.tab1.title'), href: 'tab-1' },
        { text: this.$t('targets.tab2.title'), href: 'tab-2' },
      ],
      tab: null,
    }
  },

  components: {
    ChartPracticesImplementation,
    DialogConfirm,
    FormEnvironmentalTargets,
    Fragment,
    HeaderSecondary,
    TabContainer,
    TabHeader,
  },
}
</script>
