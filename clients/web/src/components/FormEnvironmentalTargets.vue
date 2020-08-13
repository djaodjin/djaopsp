<template v-if="targets">
  <form @submit.prevent="processForm">
    <v-container>
      <v-row>
        <v-col
          class="px-0"
          cols="12"
          md="6"
          v-for="(target, index) in targets"
          :key="target.key"
        >
          <form-single-target
            :class="[index % 2 ? 'ml-md-6' : 'mr-md-6']"
            :target="target"
          />
        </v-col>
      </v-row>
    </v-container>

    <button-primary class="my-5" type="submit">{{
      $t('targets.tab1.btn-submit')
    }}</button-primary>
  </form>
</template>

<script>
import { postTargets } from '@/common/api'
import ButtonPrimary from '@/components/ButtonPrimary'
import FormSingleTarget from '@/components/FormSingleTarget'

export default {
  name: 'AssessmentEnvironmentalTargets',

  props: ['organization', 'assessment'],

  data() {
    return {
      targets: [],
    }
  },

  watch: {
    assessment: function () {
      this.targets =
        this.assessment.targets &&
        this.assessment.targets.map((target) => target.clone())
    },
  },

  methods: {
    processForm: function () {
      // TODO: form validation & do not submit targets that have been unchecked
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
    },
  },

  components: {
    ButtonPrimary,
    FormSingleTarget,
  },
}
</script>
