<template>
  <fragment>
    <v-container class="pa-0">
      <v-row align="start">
        <v-col class="pt-0 pl" cols="12" md="6">
          <question-previous-answers
            :model="model"
            :previousAnswer="previousAnswer"
          />
        </v-col>
        <v-col class="pt-md-0 text-right" cols="12" md="6">
          <button
            class="text-left mb-1"
            type="button"
            @click="isTextAreaVisible = !isTextAreaVisible"
          >
            <small
              >Would you like to comment or provide feedback related to this
              question?</small
            >
          </button>
          <v-expand-transition>
            <v-textarea
              class="comment pb-3"
              v-show="isTextAreaVisible"
              data-cy="question-footer-textarea"
              placeholder="Comments / Feedback"
              v-model="textarea"
              hide-details="auto"
              auto-grow
              outlined
              :rows="3"
              row-height="18"
              @input="$emit('textareaUpdate', textarea)"
            ></v-textarea>
          </v-expand-transition>
          <div class="mt-2">
            <button-primary type="submit" display="inline">
              <span>Save and Continue</span>
              <v-icon class="ml-2" small color="white">mdi-arrow-right</v-icon>
            </button-primary>
          </div>
        </v-col>
      </v-row>
    </v-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import ButtonPrimary from '@/components/ButtonPrimary'
import QuestionPreviousAnswers from '@/components/QuestionPreviousAnswers'

export default {
  name: 'FormQuestionFooter',

  props: {
    model: {
      type: Object,
    },
    numRows: {
      default: 2,
      type: Number,
    },
    previousAnswer: {
      // Answer
      default: null,
      type: Object,
    },
    comment: {
      type: String,
    },
  },

  data() {
    return {
      isTextAreaVisible: false,
      textarea: this.comment,
    }
  },

  components: {
    ButtonPrimary,
    Fragment,
    QuestionPreviousAnswers,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.comment {
  font-size: 0.9rem;

  & ::v-deep textarea {
    line-height: 1.6;
    color: rgba(0, 0, 0, 0.6);
  }
}

button {
  color: $primary-color;

  &:active,
  &:focus {
    outline: 0 none;
  }
}
</style>
