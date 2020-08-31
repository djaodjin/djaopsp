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
            :questions="assessment.questions"
            :answers="assessment.answers"
            :unanswered="unanswered"
            @saveAnswer="saveAnswer"
            @usePreviousAnswers="usePreviousAnswers"
          />
        </template>
        <template v-slot:tab2>
          <pending-questions
            :header="$t('practices.tab2.title')"
            :questions="unanswered"
            :answers="assessment.answers"
            @saveAnswer="saveAnswer"
          />
        </template>
      </tab-container>
      <practices-progress-indicator
        :numQuestions="assessment.questions.length"
        :numAnswers="assessment.questions.length - unanswered.length"
        :organizationId="org"
        :assessmentId="id"
      />
    </div>
    <dialog-confirm
      storageKey="previousAnswers"
      title="Previous Answers"
      actionText="Ok, thanks"
      :show="hasPreviousAnswers"
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
import { putAnswer } from '@/common/api'
import Answer from '@/common/Answer'
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
      const [organization, assessment] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.org, this.id),
      ])
      this.organization = organization
      this.assessment = assessment
      this.loading = false
    },

    saveAnswer(answer, callback) {
      putAnswer(answer)
        .then((answer) => {
          // Update in-memory answers array
          this.updateAnswersArray(answer)
          if (typeof callback === 'function') {
            callback()
          }
        })
        .catch((error) => {
          // TODO: Handle error
          console.log('Ooops ... something broke')
        })
    },

    updateAnswersArray(answer) {
      const answerIdx = this.answers.findIndex(
        (a) => a.question === answer.question && !a.frozen
      )
      if (answerIdx >= 0) {
        // Replace answer instance with a new one
        this.answers.splice(answerIdx, 1, answer)
      } else {
        this.answers.push(answer)
      }
    },

    usePreviousAnswers(questions, callback) {
      Promise.allSettled(
        questions.map((question) => {
          const previousAnswer = this.answers.find(
            (a) => a.question === question.id && a.frozen
          )
          const { id, frozen, ...attrs } = previousAnswer
          const author = 'author@email.com' // TODO: Replace with user info
          const currentAnswer = new Answer({ ...attrs, author })
          return putAnswer(currentAnswer)
        })
      ).then((answerPromises) => {
        answerPromises.forEach((answerPromise) => {
          if (answerPromise.status === 'fulfilled') {
            this.updateAnswersArray(answerPromise.value)
          }
          // TODO: Consider case where one or more answers may fail to save
        })
        if (typeof callback === 'function') {
          callback()
        }
      })
    },
  },

  computed: {
    unanswered() {
      const answered = this.assessment.answers.reduce((acc, answer) => {
        if (answer.answered) {
          acc.push(answer.question)
        }
        return acc
      }, [])
      return this.assessment.questions.reduce((acc, question) => {
        if (!answered.includes(question.id)) {
          acc.push(question)
        }
        return acc
      }, [])
    },
    hasPreviousAnswers() {
      // TODO: Update
      return false
      // return this.answers.some((answer) => answer.frozen)
    },
  },

  data() {
    return {
      loading: false,
      organization: {},
      assessment: {
        questions: [],
        answers: [],
      },
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
