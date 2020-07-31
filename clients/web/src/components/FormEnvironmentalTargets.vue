<template>
  <form @submit.prevent="processForm">
    <v-container>
      <v-row>
        <v-col cols="12" xl="6">
          <form-single-target
            :target="energyTarget"
            :label="$t('targets.tab1.form.cbx-energy')"
          />
        </v-col>
        <v-col cols="12" xl="6">
          <form-single-target
            :target="emissionsTarget"
            :label="$t('targets.tab1.form.cbx-emissions')"
          />
        </v-col>
        <v-col cols="12" xl="6">
          <form-single-target
            :target="waterTarget"
            :label="$t('targets.tab1.form.cbx-water')"
          />
        </v-col>
        <v-col cols="12" xl="6">
          <form-single-target
            :target="wasteTarget"
            :label="$t('targets.tab1.form.cbx-waste')"
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
import ButtonPrimary from '@/components/ButtonPrimary'
import FormSingleTarget from '@/components/FormSingleTarget'

export default {
  name: 'AssessmentEnvironmentalTargets',

  props: ['assessmentId'],

  data() {
    return {
      energyTarget: {
        include: true,
        dateBy: null,
        dateBaseline: null,
        text: '',
        comments: '',
      },
      emissionsTarget: {
        include: true,
        dateBy: null,
        dateBaseline: null,
        text: '',
        comments: '',
      },
      waterTarget: {
        include: true,
        dateBy: null,
        dateBaseline: null,
        text: '',
        comments: '',
      },
      wasteTarget: {
        include: true,
        dateBy: null,
        dateBaseline: null,
        text: '',
        comments: '',
      },
    }
  },

  methods: {
    processForm: function () {
      console.log('form submitted:')
      console.log(this.energyTarget)
      console.log(this.emissionsTarget)
      console.log(this.waterTarget)
      console.log(this.wasteTarget)

      this.$router.push({
        name: 'assessmentHome',
        params: { id: this.assessmentId },
      })
    },
  },

  components: {
    ButtonPrimary,
    FormSingleTarget,
  },
}
</script>
