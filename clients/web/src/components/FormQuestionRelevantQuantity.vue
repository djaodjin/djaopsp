<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row>
        <v-col data-cy="quantity" cols="12" sm="4">
          <v-text-field
            outlined
            v-model="textAnswer"
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
            v-model="relevance"
            hide-details="auto"
          ></v-select>
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
  name: 'FormQuestionQuantity',

  props: ['question', 'answer', 'previousAnswer', 'model'],

  methods: {
    processForm: function () {
      const answers = [
        this.textAnswer,
        this.model.unit.value,
        this.relevance,
        this.comment,
      ]
      const isEmpty = this.model.isEmpty(answers)
      this.$emit('submit', answers, isEmpty)
    },
    updateComment(value) {
      this.comment = value
    },
  },

  data() {
    const [textAnswer, _, relevance, comment] = this.answer.answers
    return {
      textAnswer: textAnswer || 0,
      relevance,
      comment,
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
