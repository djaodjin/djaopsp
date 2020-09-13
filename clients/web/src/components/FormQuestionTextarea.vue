<template>
  <form @submit.prevent="processForm">
    <form-question-footer
      :previousAnswer="previousAnswer"
      :questionType="question.type"
      :textareaPlaceholder="question.placeholder"
      :textareaValue="textAnswer"
      :numRows="8"
      :focus="true"
      @textareaUpdate="updateAnswer"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionTextarea',

  props: ['question', 'answer', 'previousAnswer', 'isEmpty'],

  methods: {
    processForm: function () {
      const answers = [this.textAnswer]
      const isEmpty = this.isEmpty(answers)
      this.$emit('submit', answers, isEmpty)
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
