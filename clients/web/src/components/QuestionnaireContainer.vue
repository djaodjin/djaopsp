<template v-if="currentQuestion">
  <div>
    <practice-section-header
      :category="currentQuestion.section.name"
      :title="currentQuestion.subcategory.name"
    />
    <p class="mt-3">{{ currentQuestion.text }}</p>
    <span
      class="d-block mb-4"
      style="font-size: 0.9rem;"
      v-if="currentQuestion.optional"
    >
      <sup>*</sup>This answer will not affect your score</span
    >

    <component
      :is="questionForm.name"
      :question="currentQuestion"
      :options="questionForm.options"
      :key="currentQuestion.id"
      @submit="getNextQuestion"
    />
  </div>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config'
import FormQuestionRadio from '@/components/FormQuestionRadio'
import FormQuestionTextarea from '@/components/FormQuestionTextarea'
import FormQuestionQuantity from '@/components/FormQuestionQuantity'
import PracticeSectionHeader from '@/components/PracticeSectionHeader'

export default {
  name: 'QuestionnaireContainer',

  props: ['questions', 'questionId'],

  computed: {
    currentQuestionIdx() {
      return this.questions.findIndex((q) => q.id === this.questionId)
    },
    currentQuestion() {
      return this.questions[this.currentQuestionIdx]
    },
    questionForm() {
      return MAP_QUESTION_FORM_TYPES[this.currentQuestion.type]
    },
  },

  methods: {
    getNextQuestion() {
      const nextQuestionIndex =
        (this.currentQuestionIdx + 1) % this.questions.length
      const nextQuestionId = this.questions[nextQuestionIndex].id
      const queryParams = {
        ...this.$route.query,
        ...{ question: nextQuestionId },
      }
      this.$router.push({
        path: this.$route.path,
        hash: this.$route.hash,
        query: queryParams,
      })
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
