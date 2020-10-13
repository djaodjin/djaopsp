<template>
  <form @submit.prevent="processForm">
    <form-question-textarea-controlled
      :question="question"
      :answerText="answerValue.measured"
      :commentText="answerComment.measured"
      :previousAnswer="previousAnswer"
      :model="model"
      @answer:update="updateAnswer"
      @comment:update="updateComment"
    />
  </form>
</template>

<script>
import { METRIC_COMMENT } from '@/config/questionFormTypes'
import Answer from '@/common/models/Answer'
import FormQuestionTextareaControlled from '@/components/FormQuestionTextareaControlled'

export default {
  name: 'FormQuestionTextarea',

  props: ['question', 'answer', 'previousAnswer', 'model', 'isTarget'],

  methods: {
    processForm: function () {
      const answer = new Answer({
        ...this.answer,
        author: 'author@email.com', // TODO: Replace with user info
      })
      answer.update([this.answerValue, this.answerComment])
      this.$emit('submit', answer)
    },

    updateAnswer(value) {
      this.answerValue.measured = value
    },

    updateComment(value) {
      this.answerComment.measured = value
    },
  },

  data() {
    const { answers } = this.answer
    const initialAnswer = answers[0] || {
      default: true,
      metric: this.question.type,
    }
    const initialComment = answers[1] || { metric: METRIC_COMMENT }

    return {
      answerValue: { ...initialAnswer },
      answerComment: { ...initialComment },
    }
  },

  components: {
    FormQuestionTextareaControlled,
  },
}
</script>
