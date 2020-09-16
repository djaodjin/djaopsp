<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row>
        <v-col data-cy="quantity" cols="3">
          <v-text-field
            label="Quantity"
            outlined
            v-model="answerValue.measured"
            hide-details="auto"
            type="number"
            :autofocus="true"
          ></v-text-field>
        </v-col>
        <v-col data-cy="unit" cols="9">
          <v-select
            :items="model.options"
            label="Unit"
            outlined
            v-model="answerValue.unit"
            hide-details="auto"
          ></v-select>
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
import Answer from '@/common/models/Answer'
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionQuantity',

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
