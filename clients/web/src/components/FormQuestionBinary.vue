<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row align="center">
        <v-col cols="12" md="4" xl="12">
          <v-radio-group
            class="mt-0"
            v-model="answerValue.measured"
            hide-details="auto"
          >
            <v-radio
              v-for="option in model.options"
              :key="option.value"
              :value="option.value"
            >
              <template v-slot:label>
                <span v-html="option.text"></span>
              </template>
            </v-radio>
            <v-radio
              v-if="question.optional"
              label="We're not tracking this information"
              value="no-information"
            ></v-radio>
          </v-radio-group>
        </v-col>
        <v-col cols="12" md="8" xl="6">
          <v-text-field
            label="URL/Details"
            outlined
            v-model="answerText.measured"
            hide-details="auto"
            placeholder="Please enter URL or provide more details"
            :autofocus="true"
          />
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
import { METRIC_COMMENT, METRIC_FREETEXT } from '@/config/questionFormTypes'
import Answer from '@/common/models/Answer'
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionBinary',

  props: ['question', 'answer', 'previousAnswer', 'model'],

  methods: {
    processForm: function () {
      const answer = new Answer({
        ...this.answer,
        author: 'author@email.com', // TODO: Replace with user info
      })
      answer.update([this.answerValue, this.answerText, this.answerComment])
      this.$emit('submit', answer)
    },
    updateComment(value) {
      this.answerComment.measured = value
    },
  },

  data() {
    const { answers } = this.answer
    const initialAnswer = answers[0] || {}
    const initialText =
      answers.find((answer) => answer.metric === METRIC_FREETEXT) || {}
    const initialComment =
      answers.find((answer) => answer.metric === METRIC_COMMENT) || {}

    return {
      // Copy all values so form data can safely be edited
      answerValue: { ...initialAnswer },
      answerText: { ...initialText },
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
</style>
