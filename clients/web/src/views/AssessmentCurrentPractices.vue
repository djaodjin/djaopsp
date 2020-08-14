<template>
  <fragment>
    <header-secondary
      class="container"
      :orgName="organization.name"
      :industryName="assessment.industryName"
      title="Current Practices"
    />
    <div v-if="loading">
      <loading-spinner />
    </div>
    <div v-else>
      <tab-container class="pb-16" :tabs="tabs" :rightColHidden="true">
        <template v-slot:tab1>
          <assessment-sections
            :header="$t('practices.tab1.title')"
            :questions="questions"
            :unanswered="unanswered"
          />
        </template>
        <template v-slot:tab2>
          <pending-questions
            :header="$t('practices.tab2.title')"
            :questions="unanswered"
          />
        </template>
      </tab-container>
      <practices-progress-indicator
        :numQuestions="questions.length"
        :numAnswers="questions.length - unanswered.length"
        :assessmentId="id"
      />
    </div>
    <dialog-confirm
      storageKey="previousAnswers"
      :checkStateAsync="hasPreviousAnswers"
      title="Previous Answers"
      actionText="Ok, thanks"
    >
      <p>
        Your organization has submitted a similar questionnaire in the past (per
        the industry segment selected).
      </p>
      <p>
        For each question, you will be presented the answer submitted in the
        previous questionnaire to use as reference, if there was one.
      </p>
    </dialog-confirm>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import { getQuestions } from '@/common/api'
import PracticesProgressIndicator from '@/components/PracticesProgressIndicator'
import AssessmentSections from '@/components/AssessmentSections'
import DialogConfirm from '@/components/DialogConfirm'
import HeaderSecondary from '@/components/HeaderSecondary'
import LoadingSpinner from '@/components/LoadingSpinner'
import PendingQuestions from '@/components/PendingQuestions'
import TabContainer from '@/components/TabContainer'

export default {
  name: 'AssessmentCurrentPractices',

  props: ['org', 'id'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.loading = true
      const [organization, assessment, questions] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
        getQuestions(this.org, this.id),
      ])

      this.organization = organization
      this.assessment = assessment
      this.questions = questions
      this.loading = false
    },
  },

  computed: {
    unanswered() {
      return this.questions.filter((question) => !question.currentAnswer)
    },
    hasPreviousAnswers() {
      return this.questions.some((question) => question.previousAnswers.length)
    },
  },

  data() {
    return {
      loading: false,
      organization: {},
      assessment: {},
      questions: [],
      tabs: [
        { text: this.$t('practices.tab1.title'), href: 'tab-1' },
        { text: this.$t('practices.tab2.title'), href: 'tab-2' },
      ],
    }
  },

  components: {
    Fragment,
    PracticesProgressIndicator,
    AssessmentSections,
    DialogConfirm,
    HeaderSecondary,
    LoadingSpinner,
    PendingQuestions,
    TabContainer,
  },
}
</script>
