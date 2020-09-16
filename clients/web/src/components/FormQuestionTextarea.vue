<template>
  <form @submit.prevent="processForm">
    <v-textarea
      class="pb-3"
      data-cy="question-footer-textarea"
      v-model="answerValue.measured"
      hide-details="auto"
      auto-grow
      outlined
      :rows="8"
      :focus="true"
      row-height="18"
    ></v-textarea>
    <form-question-footer
      :model="model"
      :previousAnswer="previousAnswer"
      :comment="answerComment.measured"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import { METRIC_COMMENT } from '@/config/questionFormTypes'
import Answer from '@/common/models/Answer'
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionTextarea',

  props: ['question', 'answer', 'previousAnswer', 'model'],

  methods: {
    processForm: function () {
      const answer = new Answer({
        ...this.answer,
        author: 'author@email.com', // TODO: Replace with user info
      })
      answer.save([this.answerValue, this.answerComment])
      this.$emit('submit', answer)
    },

    updateComment(value) {
      this.answerComment.measured = value
    },
  },

  data() {
    const { answers } = this.answer
    const initialAnswer = answers[0] || {}
    const initialComment = answers[1] || {}

    debugger
    return {
      answerValue: { ...initialAnswer },
      answerComment: { ...initialComment },
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
