<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="assessment.industryName"
      :title="$t('share.title')"
    />
    <tab-container :tabs="tabs" :mdCol="6" :lgCol="6">
      <template v-slot:tab1>
        <tab-header :text="$t('share.tab1.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <p>{{ $t('share.tab1.intro') }}</p>
          <form-share-assessment />
        </div>
      </template>
      <template v-slot:tab2>
        <tab-header :text="$t('share.tab2.title')" />
        <div class="pa-4 pt-sm-2 px-md-8">
          <p>{{ $t('share.tab2.intro') }}</p>
          <share-history />
        </div>
      </template>
    </tab-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
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
      const [organization, assessment] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
      ])
      this.organization = organization
      this.assessment = assessment
    },
  },

  data() {
    return {
      organization: {},
      assessment: {},
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
