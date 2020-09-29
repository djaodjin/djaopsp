<template>
  <div v-bind="$attrs">
    <v-checkbox class="mt-0" hide-details v-model="isExpanded" @click="refresh">
      <template v-slot:label>
        <b>{{ question.text }}</b>
      </template>
    </v-checkbox>

    <v-expand-transition>
      <div class="pl-8 py-1" v-show="isExpanded">
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
        <FormQuestionTextarea
          v-if="isExpanded"
          :model="questionForm"
          :question="question"
          :answer="draftAnswer"
          :isTarget="true"
        />
      </div>
    </v-expand-transition>
  </div>
</template>

<script>
import { MAP_METRICS_TO_QUESTION_FORMS } from '@/config/questionFormTypes'
import FormQuestionTextarea from '@/components/FormQuestionTextarea'

export default {
  name: 'FormSingleTarget',

  props: ['answer', 'questions'],

  data() {
    return {
      isExpanded: this.answer.answered,
      areExamplesVisible: false,
      draftAnswer: this.answer.clone(),
    }
  },

  computed: {
    question() {
      return this.questions.find((q) => q.id === this.answer.question)
    },
    questionForm() {
      return MAP_METRICS_TO_QUESTION_FORMS[this.question.type]
    },
  },

  methods: {
    refresh() {
      if (!this.isExpanded) {
        // Reset answer if it's being hidden (minimized)
        // TODO: Warn users about data loss
        this.draftAnswer = this.answer.clone().reset()
      }
    },
  },

  components: {
    FormQuestionTextarea,
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
