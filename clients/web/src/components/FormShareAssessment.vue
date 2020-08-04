<template>
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
            append-outer-icon="mdi-account-group"
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
            append-outer-icon="mdi-account-box-multiple"
          ></v-autocomplete>
          <div class="pb-4 pb-xl-0">
            <v-checkbox
              v-model="otherInvites"
              hide-details
              label="Unable to find who you're looking for?"
            />
            <v-expand-transition>
              <div class="pt-3" v-show="otherInvites">
                <v-combobox
                  v-model="emails"
                  label="Emails"
                  hint="Type in the emails you wish to share with directly"
                  persistent-hint
                  multiple
                  chips
                  deletable-chips
                  type="email"
                  :disable-lookup="true"
                  append-outer-icon="mdi-pencil-box-multiple"
                >
                  <template v-slot:no-data>
                    <v-list-item>
                      <v-list-item-content>
                        <v-list-item-title>
                          Press <kbd>tab</kbd> or <kbd>enter</kbd> to add an
                          email
                        </v-list-item-title>
                      </v-list-item-content>
                    </v-list-item>
                  </template>
                  <template v-slot:append>
                    <span>&nbsp;</span>
                  </template>
                </v-combobox>
              </div>
            </v-expand-transition>
          </div>
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
      otherInvites: false,
      groupSelection: [],
      orgSelection: [],
      emails: '',
      message: '',
    }
  },

  watch: {
    organization: function (org) {
      this.message = `Hello,\n\nI would like to invite you to view the scorecard information for ${org.name}'s assessment in The Sustainability Project.\n\nThank you,`
    },
    otherInvites: function () {
      this.emails = ''
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
