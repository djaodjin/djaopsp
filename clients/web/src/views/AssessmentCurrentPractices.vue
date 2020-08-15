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
        :numQuestions="questions.length"
        :numAnswers="questions.length - unanswered.length"
        :assessmentId="id"
      />
    </div>
    <dialog-confirm
      storageKey="previousAnswers"
      :showValue="hasPreviousAnswers"
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
import { getQuestions, getAnswers, putAnswer } from '@/common/api'
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
      const [organization, assessment, questions, answers] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getAssessment(this.id),
        getQuestions(this.org, this.id),
        getAnswers(this.org, this.id),
      ])
      // The different question form components expect an answer as one of their props so
      // create placeholder answers for any questions that have not been answered

      // Start by creating a list of all the IDs of the questions that have been answered
      const answeredQuestions = answers
        .filter((answer) => !answer.frozen)
        .map((answer) => answer.question)

      // Create a placeholder answer for each question that hasn't been answered
      const placeholderAnswers = questions
        .filter((question) => !answeredQuestions.includes(question.id))
        .map(
          (question) =>
            new Answer({
              organization: organization.id,
              assessment: assessment.id,
              question: question.id,
              author: 'author@email.com', // TODO: Replace with user info
            })
        )

      this.organization = organization
      this.assessment = assessment
      this.questions = questions
      this.answers = answers.concat(placeholderAnswers)
      this.loading = false
    },

    saveAnswer(answer, callback) {
      putAnswer(answer)
        .then((answer) => {
          // Update in-memory answers array
          const answerIdx = this.answers.findIndex(
            (a) => a.question === answer.question && !answer.frozen
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
        })
        .catch((error) => {
          // TODO: Handle error
          console.log('Ooops ... something broke')
        })
    },
  },

  computed: {
    unanswered() {
      const answered = this.answers.reduce((acc, answer) => {
        if (answer.answered) {
          acc.push(answer.question)
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
    hasPreviousAnswers() {
      return this.answers.some((answer) => answer.frozen)
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
