<template>
  <div class="progress-indicator">
    <div class="bar pt-3 px-9" v-if="answered < questions">
      <v-progress-linear
        height="8"
        :value="completed"
        color="primary"
      ></v-progress-linear>
      <span class="d-block mt-2">
        {{ answered }} / {{ questions }} questions
      </span>
    </div>
    <div class="action" v-else>
      <button-primary>Submit Questionnaire</button-primary>
    </div>
  </div>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'PracticesProgressIndicator',

  props: ['answered', 'questions'],

  computed: {
    completed() {
      return Math.round((this.answered / this.questions) * 100)
    },
  },

  components: {
    ButtonPrimary,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.progress-indicator {
  position: fixed;
  bottom: #{$bottom-nav-height}px;
  width: 100%;
  background-color: white;
  z-index: 2;
  height: calc(#{$bottom-nav-height}px + 8px);
  box-shadow: 0px 2px 4px -1px rgba(0, 0, 0, 0.2),
    0px 4px 5px 0px rgba(0, 0, 0, 0.14), 0px 1px 10px 0px rgba(0, 0, 0, 0.12);
  text-align: center;

  & > .action {
    height: inherit;
    display: flex;
    justify-content: center;
    align-items: center;
    padding-left: 36px;
    padding-right: 36px;
  }
}
</style>
