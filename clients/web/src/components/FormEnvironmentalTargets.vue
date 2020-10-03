<template v-if="assessment.targetQuestions">
  <v-form ref="form" lazy-validation @submit.prevent="processForm">
    <v-container>
      <v-row v-if="draftTargets.length">
        <v-col
          class="px-0"
          cols="12"
          md="6"
          v-for="(draftTarget, index) in draftTargets"
          :key="index"
        >
          <form-single-target
            :class="[index % 2 ? 'ml-md-6' : 'mr-md-6']"
            :draftTarget="draftTarget"
            :questions="assessment.targetQuestions"
            :previousAnswers="previousTargets"
            @answer:update="updateTargetAnswer"
            @target:toggleState="toggleTarget"
          />
        </v-col>
      </v-row>
    </v-container>

    <button-primary :disabled="!isValid" class="my-5" type="submit">
      {{ $t('targets.tab1.btn-submit') }}
    </button-primary>
  </v-form>
</template>

<script>
import { postTargets } from '@/common/api'
import ButtonPrimary from '@/components/ButtonPrimary'
import FormSingleTarget from '@/components/FormSingleTarget'

export default {
  name: 'FormEnvironmentalTargets',

  props: ['organization', 'assessment', 'previousTargets'],

  data() {
    return {
      isValid: true,
      isDisableDialogOpen: false,
      draftTargets:
        this.assessment.targetAnswers?.map((a, index) => ({
          index,
          isEnabled: a.answered,
          answer: a.clone(),
        })) || [],
    }
  },

  methods: {
    processForm: function () {
      console.log('Submit form ...')
      // this.isValid = this.$refs.form.validate()
      // if (this.isValid) {
      //   postTargets(this.organization.id, this.assessment.id, this.targets)
      //     .then((assessment) => {
      //       this.$context.updateAssessment(assessment)
      //       this.$router.push({
      //         name: 'assessmentHome',
      //         params: { id: assessment.id },
      //       })
      //     })
      //     .catch((error) => {
      //       // TODO: Handle error
      //       console.log('Ooops ... something broke')
      //     })
      // }
    },
    // validateForm: function () {
    //   if (!this.isValid) {
    //     this.isValid = this.$refs.form.validate()
    //   }
    // },
    toggleTarget(targetIndex) {
      const draftTarget = this.draftTargets[targetIndex]
      draftTarget.isEnabled = !draftTarget.isEnabled
    },
    updateTargetAnswer(targetIndex, answerValues) {
      this.draftTargets[targetIndex].answer.update(answerValues)
    },
  },

  components: {
    ButtonPrimary,
    FormSingleTarget,
  },
}
</script>
