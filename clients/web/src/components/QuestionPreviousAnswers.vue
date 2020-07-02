<template>
  <div v-if="previousAnswer">
    <span class="mr-1">Previous Answer:</span>
    <b v-html="answerText"></b>
    <p class="text-caption mt-1">
      Submitted by {{ previousAnswer.author }} on
      {{ previousAnswer.date.toISOString() }} in previous sustainability
      assessment.
    </p>
  </div>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config'

export default {
  name: 'QuestionPreviousAnswers',

  props: ['answers', 'questionType'],

  computed: {
    previousAnswer() {
      return this.answers.length > 0 && this.answers[0]
    },
    answerText() {
      return (
        this.previousAnswer &&
        MAP_QUESTION_FORM_TYPES[this.questionType].render(this.previousAnswer)
      )
    },
  },
}
</script>
