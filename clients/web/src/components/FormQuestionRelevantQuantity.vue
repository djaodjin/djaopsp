<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row>
        <v-col data-cy="quantity" cols="12" sm="4">
          <v-text-field
            outlined
            v-model="answerValue.measured"
            hide-details="auto"
            type="number"
            :autofocus="true"
          >
            <template v-slot:label>
              <span v-html="model.unit.text" />
            </template>
          </v-text-field>
        </v-col>
        <v-col data-cy="relevance" cols="12" sm="8">
          <v-select
            :items="model.options"
            label="Relevance"
            outlined
            v-model="answerRelevance.measured"
            hide-details="auto"
          ></v-select>
        </v-col>
      </v-row>
    </v-container>
    <form-question-footer
      :model="model"
      :previousAnswer="previousAnswer"
      :comment="answerComment.measured"
      @textarea:update="updateComment"
    />
  </form>
</template>

<script>
import { METRIC_COMMENT, METRIC_RELEVANCE } from '@/config/questionFormTypes'
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
      answer.update([
        this.answerValue,
        this.answerRelevance,
        this.answerComment,
      ])
      this.$emit('submit', answer)
    },

    updateComment(value) {
      this.answerComment.measured = value
    },
  },

  data() {
    const { answers } = this.answer
    const initialAnswer = answers[0] || {
      default: true,
      metric: this.question.type,
    }
    initialAnswer.unit = this.model.unit.value
    const initialRelevance = answers.find(
      (answer) => answer.metric === METRIC_RELEVANCE
    ) || { metric: METRIC_RELEVANCE }
    const initialComment = answers.find(
      (answer) => answer.metric === METRIC_COMMENT
    ) || { metric: METRIC_COMMENT }

    return {
      // Copy all values so form data can safely be edited
      answerValue: { ...initialAnswer },
      answerRelevance: { ...initialRelevance },
      answerComment: { ...initialComment },
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
