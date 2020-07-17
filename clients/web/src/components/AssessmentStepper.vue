<template>
  <v-sheet class="pb-4" elevation="3">
    <v-stepper v-model.number="computedIndex" vertical class="py-3 px-md-3">
      <template v-for="(step, i) in ASSESSMENT_FLOW.steps">
        <fragment v-if="step.key === STEP_SHARE_KEY" :key="step.key">
          <v-stepper-step
            :editable="currentStep.key === STEP_SHARE_KEY"
            :step="i + 1"
            @click.stop="step.onClick($router, { samplePath })"
          >
            <span>{{ step.text }}</span>
            <small v-if="step === currentStep">Current step</small>
          </v-stepper-step>
        </fragment>

        <fragment v-else-if="step.key === STEP_FREEZE_KEY" :key="step.key">
          <v-stepper-step
            :editable="currentStep.key === STEP_FREEZE_KEY"
            :step="i + 1"
            @click.stop="isFreezeDialogOpen = true"
          >
            <span>{{ step.text }}</span>
            <small v-if="step === currentStep">Current step</small>
          </v-stepper-step>
          <v-stepper-content :step="i + 1" />
        </fragment>

        <fragment v-else-if="step.key === STEP_SCORECARD_KEY" :key="step.key">
          <v-stepper-step
            :editable="currentStep.key === STEP_SCORECARD_KEY"
            :step="i + 1"
            :class="{
              active: currentStepIndex >= i,
              'v-stepper__step--complete': currentStepIndex >= i,
            }"
            @click.stop="step.onClick($router, { samplePath })"
          >
            <span>{{ step.text }}</span>
            <small v-if="step === currentStep">Current step</small>
          </v-stepper-step>
          <v-stepper-content :step="i + 1" />
        </fragment>

        <fragment v-else :key="step.key">
          <v-stepper-step
            :complete="
              currentStepIndex > i && currentStep.key !== STEP_SHARE_KEY
            "
            :editable="
              currentStepIndex >= i && currentStep.key !== STEP_SHARE_KEY
            "
            :step="i + 1"
            @click.stop="step.onClick($router, { samplePath })"
          >
            <span>{{ step.text }}</span>
            <small v-if="step === currentStep">Current step</small>
          </v-stepper-step>
          <v-stepper-content :step="i + 1" />
        </fragment>
      </template>
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
        provided for your organization are true and correct to the best of your
        knowledge. Additionally, you acknowledge that the responses form a
        statement of record which current or future clients may request to
        verify.
      </p>
      <p>
        After freezing the assessment, you will still be able to review its
        scorecard, but the assessment will no longer be editable.
      </p>
    </dialog-action>
  </v-sheet>
</template>

<script>
import { Fragment } from 'vue-fragment'
import {
  ASSESSMENT_FLOW,
  STEP_SHARE_KEY,
  STEP_FREEZE_KEY,
  STEP_SCORECARD_KEY,
} from '@/config/app'
import DialogAction from '@/components/DialogAction'

export default {
  name: 'AssessmentStepper',

  props: ['assessment'],

  beforeMount() {
    ASSESSMENT_FLOW.start(this.assessment.status)
    this.currentStep = ASSESSMENT_FLOW.getStep()
    this.currentStepIndex = ASSESSMENT_FLOW.getStepIndex()
  },

  beforeDestroy() {
    ASSESSMENT_FLOW.reset()
  },

  data() {
    return {
      currentStep: null,
      currentStepIndex: 0,
      ASSESSMENT_FLOW,
      STEP_SHARE_KEY,
      STEP_FREEZE_KEY,
      STEP_SCORECARD_KEY,
      isArchiveDialogOpen: false,
      isDeleteDialogOpen: false,
      isFreezeDialogOpen: false,
    }
  },

  computed: {
    computedIndex() {
      return this.currentStepIndex + 1
    },
    samplePath() {
      return this.assessment.industryPath
    },
  },

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
    archiveAssessment() {
      this.isArchiveDialogOpen = false
    },
    deleteAssessment() {
      this.isDeleteDialogOpen = false
    },
    freezeAssessment() {
      this.isFreezeDialogOpen = false
    },
  },

  components: {
    Fragment,
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
