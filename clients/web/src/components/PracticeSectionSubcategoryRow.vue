<template>
  <fragment>
    <td class="py-2 px-6 px-sm-4 py-md-4 px-md-8">{{ question.text }}</td>
    <td
      :class="[
        hasPreviousAnswers ? 'py-2 px-3' : 'py-2 pr-3 pr-md-8',
        hasShortAnswer ? 'text-center' : 'text-left',
      ]"
    >
      <router-link
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
        <span class="answer" v-if="answerText">{{ answerText }}</span>
        <v-icon v-else color="primary">mdi-help</v-icon>
      </router-link>
    </td>
    <td
      v-if="hasPreviousAnswers"
      :class="[
        'py-2',
        'pr-3',
        'pr-md-8',
        hasShortAnswer ? 'text-center' : 'text-left',
      ]"
    >
      <span class="answer">{{ previousAnswerText }}</span>
    </td>
  </fragment>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config/app'
import { Fragment } from 'vue-fragment'

export default {
  name: 'PracticeSectionSubcategoryRow',

  props: [
    'section',
    'subcategory',
    'question',
    'answers',
    'hasPreviousAnswers',
  ],

  computed: {
    answerText() {
      const answer = this.answers.find(
        (a) => a.question === this.question.id && !a.frozen
      )
      if (!answer || !answer.answers.length) return ''
      return MAP_QUESTION_FORM_TYPES[this.question.type].render(answer.answers)
    },
    hasShortAnswer() {
      return !this.answerText ? true : this.answerText.length <= 50
    },
    previousAnswerText() {
      const answer = this.answers.find(
        (a) => a.question === this.question.id && a.frozen
      )
      if (!answer || !answer.answers.length) return ''
      return MAP_QUESTION_FORM_TYPES[this.question.type].render(answer.answers)
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
