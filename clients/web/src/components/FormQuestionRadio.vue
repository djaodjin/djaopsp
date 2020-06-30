<template>
  <form @submit.prevent="processForm">
    <v-radio-group class="mt-4 pt-0 pb-6" v-model="answer" hide-details="auto">
      <v-radio
        v-for="option in options"
        :key="option.value"
        :value="option.value"
      >
        <template v-slot:label>
          <span v-html="option.text"></span>
        </template>
      </v-radio>
      <v-radio
        v-if="question.optional"
        label="I don't know"
        value="dk"
      ></v-radio>
    </v-radio-group>
    <FormQuestionFooter
      :previousAnswers="question.answers"
      :textareaPlaceholder="question.placeholder"
      :textareaValue="question.comment"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionRadio',

  props: ['question', 'options'],

  methods: {
    processForm: function () {
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

<style lang="scss" scoped>
.v-radio {
  align-items: start;

  &::v-deep > .v-label {
    padding-top: 2px;
  }
}
</style>
