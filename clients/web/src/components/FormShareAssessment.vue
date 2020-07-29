<template>
  <!-- TODO: Refactor into target components -->
  <form @submit.prevent="processForm">
    <v-container class="pl-8 py-1">
      <v-row>
        <v-col cols="6">
          <v-text-field
            hide-details="auto"
            v-model="text"
            label="Baseline"
            readonly
          ></v-text-field>
        </v-col>
      </v-row>
    </v-container>

    <button-primary class="my-5" type="submit">Share Assessment</button-primary>
  </form>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'FormShareAssessment',

  props: ['assessment'],

  data() {
    return {
      text: 'hello',
    }
  },

  methods: {
    processForm: function () {
      console.log('form submitted: ', this.form)
      this.$router.push({
        name: 'assessmentHome',
        params: { id: this.assessment.id },
      })
    },
  },

  components: {
    ButtonPrimary,
  },
}
</script>
