<template>
  <form @submit.prevent="processForm">
    <v-radio-group
      class="mt-4 pt-0 pb-6"
      v-model="answerValue.measured"
      hide-details="auto"
    >
      <v-radio
        class="mb-3"
        v-for="option in model.options"
        :key="option.value"
        :value="option.value"
      >
        <template v-slot:label>
          <b class="radio-label mr-2">{{ option.text }}:</b>
          <small v-html="option.description"></small>
        </template>
      </v-radio>
      <v-radio
        v-if="question.optional"
        label="We're not tracking this information"
        value="no-information"
      ></v-radio>
    </v-radio-group>
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
  name: 'FormQuestionRadio',

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

<style lang="scss" scoped>
.v-radio {
  align-items: start;

  &::v-deep > .v-label {
    padding-top: 2px;
  }
}
.radio-label {
  align-self: flex-start;
  white-space: nowrap;

  & + small {
    margin-top: 1px;
  }
}
</style>
