<template v-if="assessment.targetQuestions">
  <v-form
    ref="form"
    v-model="isValid"
    lazy-validation
    @submit.prevent="processForm"
  >
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

    <button-primary :disabled="!isValid" class="my-5" type="submit">{{
      $t('targets.tab1.btn-submit')
    }}</button-primary>
  </v-form>
</template>

<script>
import API from '@/common/api'
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
    processForm: async function () {
      this.isValid = this.$refs.form.validate()
      if (this.isValid) {
        Promise.allSettled(
          this.draftTargets.map((draftTarget) => {
            if (!draftTarget.isEnabled) {
              // Save empty values in the DB
              draftTarget.answer.reset()
            }
            return API.postTarget(
              this.organization.id,
              this.assessment,
              draftTarget.answer
            )
          })
        ).then((targetPromises) => {
          // TODO: Consider case where one or more answers may fail to save
          const newTargetAnswers = targetPromises
            .filter(
              (p) => p.status === 'fulfilled' && typeof p.value !== 'boolean'
            )
            .map((p) => p.value)
          this.assessment.targetAnswers = newTargetAnswers
          this.$router.push(
            this.$routeMap.get('assessmentHome').getPath({
              org: organization.id,
              slug: assessment.slug,
              industryPath: assessment.industryPath,
            })
          )
        })
      }
    },
    validateForm: function () {
      if (!this.isValid) {
        this.isValid = this.$refs.form.validate()
      }
    },
    toggleTarget(targetIndex) {
      const draftTarget = this.draftTargets[targetIndex]
      draftTarget.isEnabled = !draftTarget.isEnabled
      this.validateForm()
    },
    updateTargetAnswer(targetIndex, answerValues) {
      this.draftTargets[targetIndex].answer.update(answerValues)
      this.validateForm()
    },
  },

  components: {
    ButtonPrimary,
    FormSingleTarget,
  },
}
</script>
