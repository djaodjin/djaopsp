<template>
  <form @submit.prevent="processForm">
    <v-radio-group class="mt-4 pt-0 pb-6" v-model="answer" hide-details="auto">
      <v-radio label="Yes" value="yes"></v-radio>
      <v-radio label="Mostly Yes" value="most-yes"></v-radio>
      <v-radio label="Mostly No" value="most-no"></v-radio>
      <v-radio label="No" value="no"></v-radio>
      <v-radio label="Not Applicable" value="not-app"></v-radio>
    </v-radio-group>
    <FormQuestionFooter
      :textareaPlaceholder="question.textareaPlaceholder"
      :textareaValue="question.comment"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionRadioDiscrete',

  props: ['question'],

  methods: {
    processForm: function () {
      console.log('process form: radio discrete')
      console.log('answer: ', this.answer)
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
      comment: this.question.comment,
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
