<template>
  <!-- TODO: Refactor into target components -->
  <form @submit.prevent="processForm">
    <v-container class="pt-0">
      <v-row>
        <v-col cols="12" xl="6">
          <v-autocomplete
            v-model="groupSelection"
            :items="groups"
            :return-object="true"
            chips
            deletable-chips
            color="primary"
            hide-details="auto"
            item-text="name"
            label="Groups"
            multiple
            placeholder="Select groups"
          ></v-autocomplete>
          <v-autocomplete
            class="my-6"
            v-model="orgSelection"
            :items="organizations"
            :return-object="true"
            chips
            deletable-chips
            color="primary"
            hide-details="auto"
            item-text="name"
            label="Organizations"
            multiple
            placeholder="Select organizations"
          ></v-autocomplete>
        </v-col>
        <v-col cols="12" xl="6">
          <v-textarea
            v-model="message"
            label="Message (editable)"
            hide-details="auto"
            auto-grow
            outlined
            rows="12"
            row-height="18"
          ></v-textarea>
          <v-checkbox v-model="agreement" hide-details>
            <template v-slot:label>
              <span
                >I agree to share a copy of the assessment with the selected
                organization(s)</span
              >
            </template>
          </v-checkbox>
        </v-col>
      </v-row>
    </v-container>

    <button-primary :disabled="!agreement" class="my-4" type="submit"
      >Share Assessment</button-primary
    >
  </form>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'FormShareAssessment',

  props: ['organization', 'assessment', 'groups', 'organizations'],

  data() {
    return {
      agreement: false,
      groupSelection: [],
      orgSelection: [],
      message: '',
    }
  },

  watch: {
    organization: function (org) {
      this.message = `Hello,\n\nI would like to invite you to view the scorecard information for ${org.name}'s assessment in The Sustainability Project.\n\nThank you,`
    },
  },

  methods: {
    processForm: function () {
      console.log('validate form content and submit')
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
