<template>
  <fragment>
    <v-textarea
      :placeholder="textareaPlaceholder"
      v-model="textarea"
      hide-details="auto"
      auto-grow
      outlined
      :rows="numRows"
      row-height="16"
      @input="$emit('textareaUpdate', textarea)"
    ></v-textarea>
    <div class="mt-4 text-right">
      <button-primary type="submit" display="inline">
        <span>Answer Next Question</span>
        <v-icon class="ml-2" small color="white">mdi-arrow-right</v-icon>
      </button-primary>
    </div>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'FormQuestionFooter',

  props: {
    textareaPlaceholder: {
      type: String,
      required: true,
    },
    textareaValue: {
      type: String,
    },
    numRows: {
      type: Number,
      default: 2,
    },
  },

  data() {
    return {
      textarea: this.textareaValue,
    }
  },

  components: {
    ButtonPrimary,
    Fragment,
  },
}
</script>
