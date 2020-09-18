<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row>
        <v-col data-cy="number" cols="4">
          <v-text-field
            :label="model.options"
            outlined
            v-model="answerText.measured"
            hide-details="auto"
            type="number"
            :autofocus="true"
          ></v-text-field>
        </v-col>
      </v-row>
    </v-container>
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
  name: 'FormQuestionNumber',

  props: ['question', 'answer', 'previousAnswer', 'model'],

  methods: {
    processForm: function () {
      const answer = new Answer({
        ...this.answer,
        author: 'author@email.com', // TODO: Replace with user info
      })
      answer.update([this.answerText, this.answerComment])
      this.$emit('submit', answer)
    },

    updateComment(value) {
      this.answerComment.measured = value
    },
  },

  data() {
    const { answers } = this.answer
    const initialText = answers[0] || {
      default: true,
      metric: this.question.type,
    }
    const initialComment = answers[1] || { metric: METRIC_COMMENT }

    return {
      answerText: { ...initialText },
      answerComment: { ...initialComment },
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
