<template>
  <fragment>
    <td class="py-2 px-4">{{ question.text }}</td>
    <td :class="['py-2', 'pr-3', hasShortAnswer ? 'text-center' : 'text-left']">
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
        <span v-if="answerText">{{ answerText }}</span>
        <v-icon v-else color="primary">mdi-help</v-icon>
      </router-link>
    </td>
  </fragment>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config'
import { Fragment } from 'vue-fragment'

export default {
  name: 'PracticeSectionSubcategoryRow',

  props: ['section', 'subcategory', 'question', 'answers'],

  computed: {
    answerText() {
      const answer = this.answers.find((a) => a.questionId === this.question.id)
      if (!answer) return null
      return MAP_QUESTION_FORM_TYPES[answer.questionType].render(answer.answers)
    },
    hasShortAnswer() {
      return !this.answerText ? true : this.answerText.length <= 50
    },
  },

  components: {
    Fragment,
  },
}
</script>
