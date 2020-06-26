<template>
  <v-sheet class="pb-4" elevation="3">
    <v-stepper v-model.number="currentStep" vertical class="pt-3 pb-3">
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
            By freezing the assessment, you certify that the assessment
            responses provided for your organization are true and correct to the
            best of your knowledge. Additionally, you acknowledge that the
            responses form a statement of record which current or future clients
            may request to verify.
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
    <div class="actions text-right mt-2 mr-2">
      <v-btn text color="primary">
        <v-icon small>mdi-download</v-icon>
        <span class="ml-1">Download</span>
      </v-btn>
      |
      <v-btn
        v-if="currentStep <= 5"
        text
        color="primary"
        @click.stop="isDeleteDialogOpen = true"
      >
        <v-icon small>mdi-trash-can</v-icon>
        <span class="ml-1">Delete</span>
      </v-btn>
      <v-btn
        v-else
        text
        color="primary"
        @click.stop="isArchiveDialogOpen = true"
      >
        <v-icon small>mdi-folder-open</v-icon>
        <span class="ml-1">Archive</span>
      </v-btn>
    </div>
    <dialog-action
      title="Delete Assessment"
      actionText="Yes, delete the assessment"
      :isOpen="isDeleteDialogOpen"
      @action="deleteAssessment"
      @cancel="closeDeleteDialog"
    >
      <p>Are you sure you want to delete this assessment?</p>
      <p>The assessment will be completely removed from the TSP platform</p>
    </dialog-action>
    <dialog-action
      title="Archive Assessment"
      actionText="Yes, archive the assessment"
      :isOpen="isArchiveDialogOpen"
      @action="archiveAssessment"
      @cancel="closeArchiveDialog"
    >
      <p>
        Would you like to remove the assessment from your list of active
        assessments?
      </p>
      <p>
        You will still have access to the assessment from the assessment history
      </p>
    </dialog-action>
  </v-sheet>
</template>

<script>
import DialogAction from '@/components/DialogAction'

export default {
  name: 'AssessmentStepper',

  data: () => ({
    currentStep: 6,
    isArchiveDialogOpen: false,
    isDeleteDialogOpen: false,
    isFreezeDialogOpen: false,
  }),

  methods: {
    closeArchiveDialog() {
      this.isArchiveDialogOpen = false
    },
    closeDeleteDialog() {
      this.isDeleteDialogOpen = false
    },
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
    archiveAssessment() {
      this.isArchiveDialogOpen = false
    },
    deleteAssessment() {
      this.isDeleteDialogOpen = false
    },
    freezeAssessment() {
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
.v-sheet {
  .v-stepper {
    box-shadow: none;
  }
  & ::v-deep .v-stepper__label {
    font-size: 1.1rem;
  }
  .active ::v-deep .v-stepper__step__step {
    background-color: $primary-color !important;
    border-color: $primary-color !important;
  }

  .actions {
    span {
      font-size: 0.9rem;
    }
  }
}
</style>
