<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row>
        <v-col cols="3">
          <v-text-field
            label="Quantity"
            outlined
            v-model="answer"
            hide-details="auto"
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
    <FormQuestionFooter
      :previousAnswers="question.previousAnswers"
      :questionType="question.type"
      :textareaPlaceholder="question.placeholder"
      :textareaValue="question.comment"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionQuantity',

  props: ['question', 'options'],

  methods: {
    processForm: function () {
      console.log('answer: ', this.answer)
      console.log('unit: ', this.unit)
      console.log('comment: ', this.comment)
      this.$emit('submit')
    },
    updateComment(value) {
      this.comment = value
    },
  },

  data() {
    return {
      answer: this.question.answer,
      unit: this.question.unit,
      comment: this.question.comment,
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
