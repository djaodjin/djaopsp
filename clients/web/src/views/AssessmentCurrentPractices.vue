<template>
  <fragment>
    <section-title title="Current Practices" />
    <div v-if="loading">
      <span>Loading ...</span>
    </div>
    <template v-else>
      <tab-container :tabs="tabs">
        <template v-slot:tab1>
          <assessment-sections :questions="questions" />
        </template>
        <template v-slot:tab2>
          <pending-questions :questions="unanswered" />
        </template>
      </tab-container>
      <practices-progress-indicator questions="48" answers="46" />
    </template>
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
