<template>
  <v-stepper v-model.number="currentStep" vertical class="pb-3">
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
      @click.stop="isFreezeDialogOpen = true"
    >
      <span>Freeze assessment</span>
      <small v-if="currentStep === 5">Current step</small>
      <dialog-action
        title="Freeze Assessment"
        actionText="Yes, freeze the assessment"
        :isOpen="isFreezeDialogOpen"
        @action="freezeAssessment"
        @cancel="closeFreezeDialog"
      >
        <p>Would you like to record and freeze the assessment?</p>
        <p>
          By freezing the assessment, you certify that the assessment responses
          provided for your organization are true and correct to the best of
          your knowledge. Additionally, you acknowledge that the responses form
          a statement of record which current or future clients may request to
          verify.
        </p>
        <p>
          After freezing the assessment, you will still be able to review its
          scorecard, but the assessment will no longer be editable.
        </p>
      </dialog-action>
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
import DialogAction from '@/components/DialogAction'

export default {
  name: 'AssessmentStepper',

  data: () => ({
    currentStep: 5,
    isFreezeDialogOpen: false,
  }),

  methods: {
    closeFreezeDialog() {
      this.isFreezeDialogOpen = false
    },
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
      this.isFreezeDialogOpen = false
    },
    goToShare() {
      if (this.currentStep === 6) {
        this.$router.push({
          name: 'assessmentShare',
        })
      }
    },
  },

  components: {
    DialogAction,
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
