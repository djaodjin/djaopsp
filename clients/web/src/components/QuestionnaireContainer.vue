<template v-if="currentQuestion">
  <div class="mx-md-4">
    <practice-section-header
      :section="currentQuestion.section.name"
      :subcategory="currentQuestion.subcategory.name"
    />
    <p class="question-text mt-3 mt-md-6">{{ currentQuestion.text }}</p>
    <span
      class="d-block mb-4"
      style="font-size: 0.9rem;"
      v-if="currentQuestion.optional"
    >
      <sup>*</sup>This answer will not affect your score
    </span>

    <component
      :is="questionForm.name"
      :question="currentQuestion"
      :answer="currentAnswer"
      :options="questionForm.options"
      :key="currentQuestion.id"
      @submit="saveAndContinue"
    />
  </div>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config/app'
import Answer from '@/common/Answer'
import FormQuestionRadio from '@/components/FormQuestionRadio'
import FormQuestionTextarea from '@/components/FormQuestionTextarea'
import FormQuestionQuantity from '@/components/FormQuestionQuantity'
import PracticeSectionHeader from '@/components/PracticeSectionHeader'

export default {
  name: 'QuestionnaireContainer',

  props: ['questionId', 'questions'],

  computed: {
    currentQuestionIdx() {
      return this.questions.findIndex((q) => q.id === this.questionId)
    },
    currentQuestion() {
      return this.questions[this.currentQuestionIdx]
    },
    currentAnswer() {
      let answer = this.currentQuestion.currentAnswer
      if (!answer) {
        answer = new Answer({
          question: this.currentQuestion,
          author: 'author@email.com', // TODO: Replace with user info
        })
      }
      return answer
    },
    nextQuestion() {
      if (this.questions.length <= 1) return null
      const nextQuestionIndex =
        (this.currentQuestionIdx + 1) % this.questions.length
      return this.questions[nextQuestionIndex].id
    },
    questionForm() {
      return MAP_QUESTION_FORM_TYPES[this.currentQuestion.type]
    },
  },

  methods: {
    saveAndContinue(answers) {
      this.currentQuestion.currentAnswer = new Answer({
        ...this.currentAnswer,
        ...{ answers: answers },
      })
      const callback = this.nextQuestion
        ? function () {
            const queryParams = {
              ...this.$route.query,
              ...{ question: this.nextQuestion },
            }
            this.$router.push({
              path: this.$route.path,
              hash: this.$route.hash,
              query: queryParams,
            })
          }.bind(this)
        : function () {
            // There's no next question; reload the current path without query params
            this.$router.push({
              path: this.$route.path,
              hash: this.$route.hash,
            })
          }.bind(this)

      // TODO: Post answer to the backend then ...
      console.log('saving ...')
      console.log(this.currentQuestion.currentAnswer)

      callback()
    },
  },

  components: {
    FormQuestionRadio,
    FormQuestionTextarea,
    FormQuestionQuantity,
    PracticeSectionHeader,
  },
}
</script>

<style lang="scss" scoped>
@media #{map-get($display-breakpoints, 'md-and-up')} {
  .question-text {
    font-size: 1.1rem;
    line-height: 1.6;
  }
}
</style>
