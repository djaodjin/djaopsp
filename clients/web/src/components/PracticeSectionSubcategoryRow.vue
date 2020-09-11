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
  MAP_QUESTION_FORM_TYPES,
  QUESTION_COMMENT_TYPE,
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
      return MAP_QUESTION_FORM_TYPES[this.question.type].render(answer.answers)
    },
    hasTextAnswer() {
      return this.question.type === QUESTION_COMMENT_TYPE
    },
    previousAnswerText() {
      const answer = this.previousAnswers.find(
        (a) => a.question === this.question.id
      )
      return !answer || !answer.answers.length
        ? ''
        : MAP_QUESTION_FORM_TYPES[this.question.type].render(answer.answers)
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
