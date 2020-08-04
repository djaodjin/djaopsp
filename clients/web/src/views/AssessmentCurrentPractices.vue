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
      <tab-container class="pb-16" :tabs="tabs">
        <template v-slot:tab1>
          <assessment-sections
            :header="$t('practices.tab1.title')"
            :questions="questions"
            :answers="answers"
            :unanswered="unanswered"
            @saveAnswer="saveAnswer"
          />
        </template>
        <template v-slot:tab2>
          <pending-questions
            :header="$t('practices.tab2.title')"
            :questions="unanswered"
            :answers="answers"
            @saveAnswer="saveAnswer"
          />
        </template>
      </tab-container>
      <practices-progress-indicator
        :questions="questions.length"
        :answers="answers.length"
        :assessmentId="id"
      />
    </div>
    <dialog-confirm
      storageKey="previousAnswers"
      :checkStateAsync="checkPreviousAnswers"
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
import { getQuestions, getAnswers } from '../mocks/questions'
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
      const [organization, assessment, questions, answers] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
        getQuestions(),
        getAnswers(),
      ])

      this.organization = organization
      this.assessment = assessment
      this.questions = questions
      this.answers = answers
      this.loading = false
    },
    async checkPreviousAnswers() {
      // TODO: Send request to check if previous questionnaire has been submitted
      return new Promise((resolve) => {
        console.log('Check if previous answers have been submitted')
        resolve(true)
      })
    },

    saveAnswer(answer, callback) {
      // TODO: Post answer to the backend then ...
      // Update in-memory answers array
      console.log('saving ...')
      console.log(answer)

      const answerIdx = this.answers.findIndex(
        (a) => a.questionId === answer.questionId
      )
      if (answerIdx >= 0) {
        // Replace answer instance with a new one
        this.answers.splice(answerIdx, 1, answer)
      } else {
        this.answers.push(answer)
      }

      if (typeof callback === 'function') {
        callback()
      }
    },
  },

  computed: {
    unanswered() {
      const answered = this.answers.reduce((acc, answer) => {
        if (answer.answers.length > 0) {
          acc.push(answer.questionId)
        }
        return acc
      }, [])
      return this.questions.reduce((acc, question) => {
        if (!answered.includes(question.id)) {
          acc.push(question)
        }
        return acc
      }, [])
    },
  },

  data() {
    return {
      loading: false,
      organization: {},
      assessment: {},
      questions: [],
      answers: [],
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
