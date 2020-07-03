<template>
  <fragment>
    <section-title title="Current Practices" />
    <div v-if="loading">
      <span>Loading ...</span>
    </div>
    <div v-else>
      <tab-container :tabs="tabs">
        <template v-slot:tab1>
          <assessment-sections
            :questions="questions"
            :answers="answers"
            @saveAnswer="saveAnswer"
          />
        </template>
        <template v-slot:tab2>
          <pending-questions
            :questions="unanswered"
            :answers="answers"
            @saveAnswer="saveAnswer"
          />
        </template>
      </tab-container>
      <practices-progress-indicator
        :questions="questions.length"
        :answers="answers.length"
      />
    </div>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import { getQuestions, getAnswers } from '../mocks/questions'
import PracticesProgressIndicator from '@/components/PracticesProgressIndicator'
import AssessmentSections from '@/components/AssessmentSections'
import PendingQuestions from '@/components/PendingQuestions'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'

export default {
  name: 'AssessmentCurrentPractices',

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.loading = true
      this.questions = await getQuestions()
      this.answers = await getAnswers()
      this.loading = false
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
    PendingQuestions,
    SectionTitle,
    TabContainer,
  },
}
</script>
