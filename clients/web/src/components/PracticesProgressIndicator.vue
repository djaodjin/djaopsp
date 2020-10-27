<template>
  <div class="progress-indicator">
    <div class="bar pt-3 px-9" v-if="numAnswers < numQuestions">
      <v-progress-linear
        height="8"
        :value="completed"
        color="primary"
      ></v-progress-linear>
      <span class="d-block mt-2">
        {{ numAnswers }} / {{ numQuestions }} questions
      </span>
    </div>
    <div class="action" data-cy="btn-complete" v-else>
      <button-primary
        :to="`/${organizationId}/home/${assessment.slug}/${assessment.industryPath}/`"
      >
        Back to Assessment Home
      </button-primary>
    </div>
  </div>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'PracticesProgressIndicator',

  props: ['numAnswers', 'numQuestions', 'organizationId', 'assessment'],

  computed: {
    completed() {
      return this.numQuestions > 0
        ? Math.round((this.numAnswers / this.numQuestions) * 100)
        : 0
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
  left: 0;
  bottom: #{$bottom-nav-height}px;
  width: 100%;
  background-color: white;
  z-index: 5;
  height: calc(#{$bottom-nav-height}px + 8px);
  box-shadow: 0px 2px 4px -1px rgba(0, 0, 0, 0.2),
    0px 4px 5px 0px rgba(0, 0, 0, 0.14), 0px 1px 10px 0px rgba(0, 0, 0, 0.12);
  text-align: center;

  @media #{map-get($display-breakpoints, 'sm-and-up')} {
    bottom: 0;
  }

  & > .action {
    height: inherit;
    display: flex;
    justify-content: center;
    align-items: center;
    padding-left: 36px;
    padding-right: 36px;
    max-width: 580px;
    margin: 0 auto;
  }
}
</style>
