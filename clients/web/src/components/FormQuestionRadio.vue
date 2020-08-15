<template>
  <form @submit.prevent="processForm">
    <v-radio-group
      class="mt-4 pt-0 pb-6"
      v-model="selectedOption"
      hide-details="auto"
    >
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
    <form-question-footer
      :previousAnswers="question.previousAnswers"
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
  name: 'FormQuestionRadio',

  props: ['question', 'answer', 'options'],

  methods: {
    processForm: function () {
      const isEmpty = !this.selectedOption
      this.$emit('submit', [this.selectedOption, this.comment], isEmpty)
    },
    updateComment(value) {
      this.comment = value
    },
  },

  data() {
    return {
      selectedOption: this.answer.answers[0],
      comment: this.answer.answers[1],
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
