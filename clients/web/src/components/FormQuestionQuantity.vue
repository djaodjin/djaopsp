<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row>
        <v-col cols="3">
          <v-text-field
            label="Quantity"
            outlined
            v-model="textAnswer"
            hide-details="auto"
            type="number"
            :autofocus="true"
          ></v-text-field>
        </v-col>
        <v-col cols="9">
          <v-select
            :items="options"
            label="Unit"
            outlined
            v-model="unit"
            hide-details="auto"
          ></v-select>
        </v-col>
      </v-row>
    </v-container>
    <form-question-footer
      :previousAnswer="previousAnswer"
      :questionType="question.type"
      :textareaPlaceholder="question.placeholder"
      :textareaValue="comment"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionQuantity',

  props: ['question', 'answer', 'previousAnswer', 'options'],

  methods: {
    processForm: function () {
      const isEmpty = !this.textAnswer || !this.unit
      this.$emit('submit', [this.textAnswer, this.unit, this.comment], isEmpty)
    },
    updateComment(value) {
      this.comment = value
    },
  },

  data() {
    return {
      textAnswer: this.answer.answers[0],
      unit: this.answer.answers[1],
      comment: this.answer.answers[2],
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
