<template>
  <form @submit.prevent="processForm">
    <v-radio-group
      class="mt-4 pt-0 pb-6"
      v-model="selectedOption"
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

  props: ['question', 'answer', 'previousAnswer', 'model'],

  methods: {
    processForm: function () {
      const answers = [this.selectedOption, this.comment]
      const isEmpty = this.model.isEmpty(answers)
      this.$emit('submit', answers, isEmpty)
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
.radio-label {
  align-self: flex-start;
  white-space: nowrap;

  & + small {
    margin-top: 1px;
  }
}
</style>
