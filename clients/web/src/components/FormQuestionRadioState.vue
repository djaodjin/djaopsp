<template>
  <form @submit.prevent="processForm">
    <v-radio-group class="mt-4 pt-0 pb-6" v-model="answer" hide-details="auto">
      <v-radio value="initiating">
        <template v-slot:label>
          <span>
            <b class="mr-1">Initiating:</b>There is minimal management support
          </span>
        </template>
      </v-radio>
      <v-radio value="progressing">
        <template v-slot:label>
          <span>
            <b class="mr-1">Progresssing:</b>Support is visible and clearly
            demonstrated
          </span>
        </template>
      </v-radio>
      <v-radio value="optimizing">
        <template v-slot:label>
          <span>
            <b class="mr-1">Optimizing:</b>Executive management reviews
            environmental performance, risks and opportunities, and
            endorses/sets goals
          </span>
        </template>
      </v-radio>
      <v-radio value="leading">
        <template v-slot:label>
          <span>
            <b class="mr-1">Leading:</b>The Board of Directors annually reviews
            environmental performance and sets or endorses goals
          </span>
        </template>
      </v-radio>
      <v-radio value="transforming">
        <template v-slot:label>
          <span class="d-inline-block">
            <b class="mr-1">Transforming:</b>Executive management sponsors
            transformative change in industry sector and beyond
          </span>
        </template>
      </v-radio>
      <v-radio
        v-if="question.optional"
        label="I don't know"
        value="dk"
      ></v-radio>
    </v-radio-group>
    <FormQuestionFooter
      :textareaPlaceholder="question.textareaPlaceholder"
      :textareaValue="question.comment"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'
// TODO: fix vertical alignment for labels

export default {
  name: 'FormQuestionRadioState',

  props: ['question'],

  methods: {
    processForm: function () {
      console.log('answer: ', this.answer)
      console.log('comment: ', this.comment)
      this.$emit('submit')
    },
    updateComment(value) {
      this.comment = value
    },
  },

  data() {
    return {
      answer: this.question.answer,
      comment: this.question.comment,
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
