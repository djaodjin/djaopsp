<template v-if="assessment.targetQuestions">
  <v-form ref="form" lazy-validation @submit.prevent="processForm">
    <v-container>
      <v-row>
        <v-col
          class="px-0"
          cols="12"
          md="6"
          v-for="(answer, index) in assessment.targetAnswers"
          :key="index"
        >
          <form-single-target
            :class="[index % 2 ? 'ml-md-6' : 'mr-md-6']"
            :answer="answer"
            :questions="assessment.targetQuestions"
            @form:validate="validateForm"
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

  props: ['organization', 'assessment'],

  data() {
    return {
      isValid: true,
    }
  },

  methods: {
    processForm: function () {
      this.isValid = this.$refs.form.validate()
      if (this.isValid) {
        postTargets(this.organization.id, this.assessment.id, this.targets)
          .then((assessment) => {
            this.$context.updateAssessment(assessment)
            this.$router.push({
              name: 'assessmentHome',
              params: { id: assessment.id },
            })
          })
          .catch((error) => {
            // TODO: Handle error
            console.log('Ooops ... something broke')
          })
      }
    },
    validateForm: function () {
      if (!this.isValid) {
        this.isValid = this.$refs.form.validate()
      }
    },
  },

  components: {
    ButtonPrimary,
    FormSingleTarget,
  },
}
</script>
