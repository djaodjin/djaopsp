<template>
  <div v-bind="$attrs">
    <v-checkbox
      class="mt-0"
      hide-details
      :input-value="draftTarget.isEnabled"
      @click="$emit('target:toggleState', draftTarget.index)"
    >
      <template v-slot:label>
        <b>{{ question.text }}</b>
      </template>
    </v-checkbox>

    <v-expand-transition>
      <div class="pl-8 py-1" v-show="draftTarget.isEnabled">
        <div class="my-3 examples">
          <span>
            Need help writing your target?
            <button
              type="button"
              @click="areExamplesVisible = !areExamplesVisible"
            >
              View some examples.
            </button>
          </span>
          <v-expand-transition>
            <ul class="ml-4" v-show="areExamplesVisible">
              <li class="mt-2">
                Donec accumsan ipsum ac nibh gravida ornare. Duis eget consequat
                enim. Sed non lorem sed mauris vestibulum tempus nec nec risus.
                Mauris vel dolor turpis.
              </li>
              <li class="mt-2">
                Vivamus faucibus metus a dui fringilla sodales. Aenean lectus
                felis, scelerisque sed consectetur eu, elementum quis risus. Ut
                et pretium nisl. Nam metus elit, ultricies interdum tortor ac,
                placerat bibendum urna.
              </li>
            </ul>
          </v-expand-transition>
        </div>
        <form-question-textarea-controlled
          :question="question"
          :answerText="answerValue.measured"
          :commentText="answerComment.measured"
          :previousAnswer="previousAnswer"
          :model="questionForm"
          :isTarget="true"
          :isRequired="draftTarget.isEnabled"
          errorMessage="Please provide a target or unselect it."
          @answer:update="updateAnswer"
          @comment:update="updateComment"
        />
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import { MAP_METRICS_TO_QUESTION_FORMS } from '@/config/questionFormTypes'
import FormQuestionTextareaControlled from '@/components/FormQuestionTextareaControlled'

export default {
  name: 'FormSingleTarget',

  props: ['draftTarget', 'questions', 'previousAnswers'],

  data() {
    const { answers } = this.draftTarget.answer

    return {
      areExamplesVisible: false,
      answerValue: { ...answers[0] } || {
        default: true,
        metric: this.question.type,
        mesured: '',
      },
      answerComment: { ...answers[1] } || {
        metric: METRIC_COMMENT,
        mesured: '',
      },
    }
  },

  computed: {
    question() {
      const question = this.draftTarget.answer.question
      return this.questions.find((q) => q.id === question)
    },
    questionForm() {
      return MAP_METRICS_TO_QUESTION_FORMS[this.question.type]
    },
    previousAnswer() {
      return this.previousAnswers.find((a) => a.question === this.question.id)
    },
  },

  methods: {
    processForm: function () {
      const answer = new Answer({
        ...this.answer,
        author: 'author@email.com', // TODO: Replace with user info
      })
      answer.update()
      this.$emit('submit', answer)
    },

    updateAnswer(value) {
      this.answerValue.measured = value
      this.$emit('answer:update', this.draftTarget.index, [
        this.answerValue,
        this.answerComment,
      ])
    },

    updateComment(value) {
      this.answerComment.measured = value
      this.$emit('answer:update', this.draftTarget.index, [
        this.answerValue,
        this.answerComment,
      ])
    },
  },

  components: {
    FormQuestionTextareaControlled,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.examples {
  font-size: 0.9rem;

  button {
    color: $primary-color;

    &:active,
    &:focus {
      outline: 0 none;
    }
  }

  ul {
    list-style: disc;
  }
}
</style>
