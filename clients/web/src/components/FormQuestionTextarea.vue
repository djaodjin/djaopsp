<template>
  <form @submit.prevent="processForm">
    <FormQuestionFooter
      :textareaPlaceholder="question.placeholder"
      :textareaValue="question.answer"
      :numRows="8"
      @textareaUpdate="updateAnswer"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionTextarea',

  props: ['question'],

  methods: {
    processForm: function () {
      console.log('answer: ', this.answer)
      this.$emit('submit')
    },
    updateAnswer(value) {
      this.answer = value
    },
  },

  data() {
    return {
      answer: this.question.answer,
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
