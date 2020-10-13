<template>
  <v-card outlined class="d-inline-block py-3 px-4">
    <span class="mr-1">Previous Answer:</span>
    <b v-html="answerText" />
    <p class="text-caption mt-1 mb-0">
      Submitted by {{ previousAnswer.author }} on
      <span v-format-date>{{ previousAnswer.created }}</span> in previous
      sustainability assessment.
    </p>
  </v-card>
</template>

<script>
import { formatDate } from '@/directives'

export default {
  name: 'QuestionPreviousAnswers',

  props: ['model', 'previousAnswer'],

  computed: {
    answerText() {
      return this.previousAnswer && this.previousAnswer.render()
    },
  },

  directives: {
    formatDate,
  },
}
</script>
