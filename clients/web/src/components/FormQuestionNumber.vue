<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row>
        <v-col data-cy="number" cols="4">
          <v-text-field
            :label="model.options"
            outlined
            v-model="textAnswer"
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
      :textareaPlaceholder="question.placeholder"
      :textareaValue="comment"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionNumber',

  props: ['question', 'answer', 'previousAnswer', 'model'],

  methods: {
    processForm: function () {
      const answers = [this.textAnswer, this.comment]
      const isEmpty = this.model.isEmpty(answers)
      this.$emit('submit', answers, isEmpty)
    },
    updateComment(value) {
      this.comment = value
    },
  },

  data() {
    return {
      textAnswer: this.answer.answers[0],
      comment: this.answer.answers[1],
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
