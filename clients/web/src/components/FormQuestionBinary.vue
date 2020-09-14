<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row align="center">
        <v-col cols="12" md="4" xl="12">
          <v-radio-group
            class="mt-0"
            v-model="selectedOption"
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
            v-model="textAnswer"
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
      :textareaPlaceholder="question.placeholder"
      :textareaValue="comment"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionBinary',

  props: ['question', 'answer', 'previousAnswer', 'model'],

  methods: {
    processForm: function () {
      const answers = [this.selectedOption, this.textAnswer, this.comment]
      const isEmpty = this.model.isEmpty(answers)
      this.$emit('submit', answers, isEmpty)
    },
    updateComment(value) {
      this.comment = value
    },
  },

  data() {
    const [selectedOption, textAnswer = '', comment = ''] = this.answer.answers
    return {
      selectedOption,
      textAnswer,
      comment,
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
