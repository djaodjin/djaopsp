<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="assessment.industryName"
      :title="$t('targets.title')"
    />
    <tab-container :tabs="tabs" :xlLeftCol="8" :xlRightCol="4">
      <template v-slot:tab1>
        <tab-header :text="$t('targets.tab1.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <p class="mb-0">{{ $t('targets.tab1.intro') }}</p>
          <form-environmental-targets
            :organization="organization"
            :assessment="assessment"
          />
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
          <v-container>
            <v-row>
              <v-col
                cols="12"
                sm="6"
                xl="12"
                v-for="(benchmark, index) in score.benchmarks"
                :key="index"
              >
                <chart-practices-implementation
                  :class="[index % 2 ? 'ml-sm-3 ml-md-6' : 'mr-sm-3 mr-md-6']"
                  :section="benchmark.section"
                  :scores="benchmark.scores"
                  :companyScore="benchmark.companyScore"
                />
              </v-col>
            </v-row>
          </v-container>
        </div>
      </template>
    </tab-container>
    <dialog-confirm
      storageKey="previousTargets"
      title="Previous Targets"
      actionText="Ok, thanks"
      :show="hasPreviousTargets"
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
        this.$context.getAssessment(this.org, this.id),
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
      hasPreviousTargets: false, // TODO: compute this value after getting previous targets
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
