<template>
  <fragment>
    <td class="py-2 pl-6 pr-2 px-sm-4 py-md-4 px-md-8">{{ question.text }}</td>
    <td
      :class="[
        hasTextAnswer ? 'text-left' : 'text-center',
        'py-2 px-3 px-md-4',
      ]"
    >
      <router-link
        data-cy="answer-link"
        :style="[!answerText ? { 'text-decoration': 'none' } : {}]"
        :to="{
          path: `${$route.path}${$route.hash}`,
          query: {
            section: section.id,
            subcategory: subcategory.id,
            question: question.id,
          },
        }"
      >
        <span class="answer" v-if="answerText" v-html="answerText" />
        <v-icon v-else color="primary">mdi-help</v-icon>
      </router-link>
    </td>
    <td
      v-if="hasPreviousAnswers"
      :class="[
        hasTextAnswer ? 'text-left' : 'text-center',
        'py-2 px-3 px-md-4',
      ]"
      data-cy="previous-answer"
    >
      <span class="answer" v-html="previousAnswerText" />
    </td>
  </fragment>
</template>

<script>
import {
  MAP_METRICS_TO_QUESTION_FORMS,
  METRIC_FREETEXT,
} from '@/config/questionFormTypes'
import { Fragment } from 'vue-fragment'

export default {
  name: 'PracticeSectionSubcategoryRow',

  props: [
    'section',
    'subcategory',
    'question',
    'answers',
    'previousAnswers',
    'hasPreviousAnswers',
  ],

  computed: {
    answerText() {
      const answer = this.answers.find((a) => a.question === this.question.id)
      if (!answer || !answer.answers.length) return ''
      return MAP_METRICS_TO_QUESTION_FORMS[this.question.type].render(
        answer.answers
      )
    },
    hasTextAnswer() {
      return this.question.type === METRIC_FREETEXT
    },
    previousAnswerText() {
      const answer = this.previousAnswers.find(
        (a) => a.question === this.question.id
      )
      return !answer || !answer.answers.length
        ? ''
        : MAP_METRICS_TO_QUESTION_FORMS[this.question.type].render(
            answer.answers
          )
    },
  },

  components: {
    Fragment,
  },
}
</script>

<style lang="scss" scoped>
.answer {
  font-size: 0.9rem;
}
</style>
