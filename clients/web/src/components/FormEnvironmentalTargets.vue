<template v-if="targets">
  <form @submit.prevent="processForm">
    <v-container>
      <v-row>
        <v-col
          class="px-0"
          cols="12"
          xl="6"
          v-for="target in targets"
          :key="target.key"
        >
          <form-single-target :target="target" />
        </v-col>
      </v-row>
    </v-container>

    <button-primary class="my-5" type="submit">{{
      $t('targets.tab1.btn-submit')
    }}</button-primary>
  </form>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'
import FormSingleTarget from '@/components/FormSingleTarget'

export default {
  name: 'AssessmentEnvironmentalTargets',

  props: ['assessment'],

  computed: {
    targets() {
      return (
        this.assessment.targets &&
        this.assessment.targets.map((target) => target.clone())
      )
    },
  },

  methods: {
    processForm: function () {
      // TODO: form validation & do not submit targets that have been unchecked
      console.log('form submitted:')
      console.log(this.targets)

      this.$router.push({
        name: 'assessmentHome',
        params: { id: this.assessment.id },
      })
    },
  },

  components: {
    ButtonPrimary,
    FormSingleTarget,
  },
}
</script>
