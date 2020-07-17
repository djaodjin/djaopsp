<template>
  <form @submit.prevent="processForm">
    <FormQuestionFooter
      :previousAnswers="question.previousAnswers"
      :questionType="question.type"
      :textareaPlaceholder="question.placeholder"
      :textareaValue="textAnswer"
      :numRows="8"
      @textareaUpdate="updateAnswer"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionTextarea',

  props: ['question', 'answer'],

  methods: {
    processForm: function () {
      this.$emit('submit', [this.textAnswer])
    },
    updateAnswer(value) {
      this.textAnswer = value
    },
  },

  data() {
    return {
      textAnswer: this.answer.answers[0],
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
