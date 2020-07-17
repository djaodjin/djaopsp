<template>
  <div v-if="previousAnswer">
    <span class="mr-1">Previous Answer:</span>
    <b>{{ answerText }}</b>
    <p class="text-caption mt-1">
      Submitted by {{ previousAnswer.author }} on
      {{ previousAnswer.modified.toISOString() }} in previous sustainability
      assessment.
    </p>
  </div>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config/app'

export default {
  name: 'QuestionPreviousAnswers',

  props: ['answers'],

  computed: {
    previousAnswer() {
      return this.answers.length > 0 && this.answers[0]
    },
    answerText() {
      return (
        this.previousAnswer &&
        MAP_QUESTION_FORM_TYPES[this.previousAnswer.questionType].render(
          this.previousAnswer.answers
        )
      )
    },
  },
}
</script>
