<template>
  <v-stepper v-model="currentStep" vertical class="pb-3">
    <v-stepper-step
      :complete="currentStep > 1 && currentStep < 6"
      :editable="currentStep < 6"
      step="1"
      @click.stop="goToCurrentPractices"
    >
      <span>Establish current practices</span>
      <small v-if="currentStep === 1">Current step</small>
    </v-stepper-step>
    <v-stepper-content step="1" />

    <v-stepper-step
      :complete="currentStep > 2 && currentStep < 6"
      :editable="currentStep >= 2 && currentStep < 6"
      step="2"
      @click.stop="goToTargets"
    >
      <span>Define environmental targets</span>
      <small v-if="currentStep === 2">Current step</small>
    </v-stepper-step>
    <v-stepper-content step="2" />

    <v-stepper-step
      :complete="currentStep > 3 && currentStep < 6"
      :editable="currentStep >= 3 && currentStep < 6"
      step="3"
      @click.stop="goToImprovementPlan"
    >
      <span>Create improvement plan</span>
      <small v-if="currentStep === 3">Current step</small>
    </v-stepper-step>
    <v-stepper-content step="3" />

    <v-stepper-step
      :editable="currentStep >= 4"
      step="4"
      :class="{
        active: currentStep >= 4,
        'v-stepper__step--complete': currentStep >= 4,
      }"
      @click.stop="goToScorecard"
    >
      <span>Review scorecard</span>
      <small v-if="currentStep === 4">Current step</small>
    </v-stepper-step>
    <v-stepper-content step="4" />

    <v-stepper-step
      :editable="currentStep === 5"
      step="5"
      @click.stop="freezeAssessment"
    >
      <span>Freeze assessment</span>
      <small v-if="currentStep === 5">Current step</small>
    </v-stepper-step>
    <v-stepper-content step="5" />

    <v-stepper-step
      :editable="currentStep === 6"
      step="6"
      @click.stop="goToShare"
    >
      <span>Share assessment</span>
      <small v-if="currentStep === 6">Current step</small>
    </v-stepper-step>
  </v-stepper>
</template>

<script>
export default {
  name: 'ButtonPrimary',

  data: () => ({
    currentStep: 1,
  }),

  methods: {
    goToCurrentPractices() {
      if (this.currentStep < 6) {
        this.$router.push({
          name: 'introPractices',
        })
      }
    },
    goToTargets() {
      if (this.currentStep >= 2 && this.currentStep < 6) {
        this.$router.push({
          name: 'introTargets',
        })
      }
    },
    goToImprovementPlan() {
      if (this.currentStep >= 3 && this.currentStep < 6) {
        this.$router.push({
          name: 'introPlan',
        })
      }
    },
    goToScorecard() {
      if (this.currentStep >= 4) {
        this.$router.push({
          name: 'assessmentScorecard',
        })
      }
    },
    freezeAssessment() {
      console.log('Freeze assessment')
    },
    goToShare() {
      if (this.currentStep === 6) {
        this.$router.push({
          name: 'assessmentShare',
        })
      }
    },
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';
.active ::v-deep .v-stepper__step__step {
  background-color: $primary-color !important;
  border-color: $primary-color !important;
}
</style>
