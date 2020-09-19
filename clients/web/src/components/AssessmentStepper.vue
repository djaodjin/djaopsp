<template>
  <v-sheet
    class="pb-4"
    :elevation="STANDALONE ? 3 : 0"
    :outlined="!Boolean(STANDALONE)"
    data-cy="stepper"
  >
    <v-stepper v-model.number="computedIndex" vertical class="py-3 px-md-3">
      <template v-for="(step, i) in ASSESSMENT_FLOW.steps">
        <fragment v-if="step.key === STEP_SHARE_KEY" :key="step.key">
          <v-stepper-step
            color="secondary"
            :data-cy="step.key"
            :editable="currentStep.key === STEP_SHARE_KEY"
            :step="i + 1"
            @click.stop="
              step.onClick(
                $router,
                { organization, assesssment },
                currentStep.key === STEP_SHARE_KEY
              )
            "
          >
            <span>{{ step.text }}</span>
          </v-stepper-step>
        </fragment>

        <fragment v-else-if="step.key === STEP_REVIEW_KEY" :key="step.key">
          <v-stepper-step
            color="secondary"
            :data-cy="step.key"
            :editable="currentStepIndex >= i"
            :step="i + 1"
            :class="{
              active: currentStepIndex >= i,
              'v-stepper__step--complete': currentStepIndex >= i,
            }"
            @click.stop="
              step.onClick(
                $router,
                { organization, assessment },
                currentStepIndex >= i
              )
            "
          >
            <span>{{ step.text }}</span>
          </v-stepper-step>
          <v-stepper-content :step="i + 1" />
        </fragment>

        <fragment v-else :key="step.key">
          <v-stepper-step
            color="secondary"
            :data-cy="step.key"
            :complete="
              currentStepIndex > i && currentStep.key !== STEP_SHARE_KEY
            "
            :editable="
              currentStepIndex >= i && currentStep.key !== STEP_SHARE_KEY
            "
            :rules="[
              () =>
                currentStepIndex <= i ||
                currentStep.key === STEP_SHARE_KEY ||
                step.key !== STEP_TARGETS_KEY ||
                (step.key === STEP_TARGETS_KEY && assessmentHasTargets),
              () =>
                currentStepIndex <= i ||
                currentStep.key === STEP_SHARE_KEY ||
                step.key !== STEP_PLAN_KEY ||
                (step.key === STEP_PLAN_KEY &&
                  assessment.improvementPlan.length > 0),
            ]"
            error-icon="mdi-alert-circle"
            :step="i + 1"
            @click.stop="
              step.onClick(
                $router,
                { organization, assessment },
                currentStepIndex >= i && currentStep.key !== STEP_SHARE_KEY
              )
            "
          >
            <span>{{ step.text }}</span>
            <small
              v-if="step.key === STEP_TARGETS_KEY || step.key === STEP_PLAN_KEY"
              >Optional step</small
            >
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
  </v-sheet>
</template>

<script>
import { Fragment } from 'vue-fragment'
import {
  ASSESSMENT_FLOW,
  STEP_TARGETS_KEY,
  STEP_PLAN_KEY,
  STEP_SHARE_KEY,
  STEP_REVIEW_KEY,
} from '@/config/app'
import DialogAction from '@/components/DialogAction'

export default {
  name: 'AssessmentStepper',

  props: ['organization', 'assessment'],

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
      STEP_TARGETS_KEY,
      STEP_PLAN_KEY,
      STEP_SHARE_KEY,
      STEP_REVIEW_KEY,
      isArchiveDialogOpen: false,
      isDeleteDialogOpen: false,
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  computed: {
    computedIndex() {
      return this.currentStepIndex + 1
    },
    assessmentHasTargets() {
      // At least one of the targets has text
      return this.assessment.targets.some((target) => target.text)
    },
  },

  methods: {
    closeArchiveDialog() {
      this.isArchiveDialogOpen = false
    },
    closeDeleteDialog() {
      this.isDeleteDialogOpen = false
    },
    archiveAssessment() {
      this.isArchiveDialogOpen = false
    },
    deleteAssessment() {
      this.isDeleteDialogOpen = false
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
  .v-stepper__step--active ::v-deep .v-stepper__step__step {
    animation: attention 0.8s ease-out 1s infinite alternate;
  }
  & ::v-deep .v-stepper__label {
    font-size: 1.1rem;
  }
  & ::v-deep .v-stepper__step--error .v-icon {
    font-size: 1.7rem;
  }
  .active ::v-deep .v-stepper__step__step {
    background-color: $secondary-color !important;
    border-color: $secondary-color !important;
    animation: attention 0.8s ease-out 1s infinite alternate;
  }

  .actions {
    span {
      font-size: 0.9rem;
    }
  }
}

@keyframes attention {
  from {
    transform: scale(1);
  }
  to {
    transform: scale(1.2);
  }
}
</style>
