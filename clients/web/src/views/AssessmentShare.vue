<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="asssessment.industryName"
      :title="$t('share.title')"
    />
    <tab-container
      :tabs="tabs"
      :lgLeftCol="7"
      :lgRightCol="5"
      :xlLeftCol="8"
      :xlRightCol="4"
    >
      <template v-slot:tab1>
        <tab-header :text="$t('share.tab1.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <p class="mb-2">{{ $t('share.tab1.intro') }}</p>
          <form-share-assessment
            :organization="organization"
            :assessment="assessment"
            :groups="groups"
            :organizations="organizations"
          />
        </div>
      </template>
      <template v-slot:tab2>
        <tab-header :text="$t('share.tab2.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <share-history :history="history" />
        </div>
      </template>
    </tab-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import { getOrganizations, getShareHistory } from '@/common/api'
import FormShareAssessment from '@/components/FormShareAssessment'
import HeaderSecondary from '@/components/HeaderSecondary'
import ShareHistory from '@/components/ShareHistory'
import TabContainer from '@/components/TabContainer'
import TabHeader from '@/components/TabHeader'

export default {
  name: 'assessmentShare',

  props: ['org', 'id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const [
        organization,
        assessment,
        history,
        organizations,
      ] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.org, this.id),
        getShareHistory(),
        getOrganizations(),
      ])

      this.organization = organization
      this.assessment = assessment
      this.history = history
      this.groups = organizations.groups
      this.organizations = organizations.individuals
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
      history: [],
      groups: [],
      organizations: [],
      tabs: [
        { text: this.$t('share.tab1.title'), href: 'tab-1' },
        { text: this.$t('share.tab2.title'), href: 'tab-2' },
      ],
      tab: null,
    }
  },

  components: {
    FormShareAssessment,
    Fragment,
    HeaderSecondary,
    ShareHistory,
    TabContainer,
    TabHeader,
  },
}
</script>
