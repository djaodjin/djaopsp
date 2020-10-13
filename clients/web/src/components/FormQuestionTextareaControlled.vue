<template>
  <div>
    <v-textarea
      class="pb-3"
      data-cy="question-textarea"
      :value="answerText"
      hide-details="auto"
      auto-grow
      outlined
      :rows="8"
      :focus="true"
      row-height="18"
      :rules="[
        () => !isRequired || (isRequired && !!answerText) || errorMessage,
      ]"
      @input="(newValue) => $emit('answer:update', newValue)"
    ></v-textarea>
    <form-question-footer
      :model="model"
      :previousAnswer="previousAnswer"
      :comment="commentText"
      :isTarget="isTarget"
      @textarea:update="(newValue) => $emit('comment:update', newValue)"
    />
  </div>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionTextarea',

  props: [
    'question',
    'answerText',
    'commentText',
    'previousAnswer',
    'model',
    'isTarget',
    'isRequired',
    'errorMessage',
  ],

  components: {
    FormQuestionFooter,
  },
}
</script>
