<template>
  <div class="assessment-container">
    <h1 class="assessment-title">Environment Sustainability Assessment</h1>
    <div id="my-div">
      <v-container>
        <v-row justify="center">
          <v-col cols="12" md="8" lg="6">
            <form @submit.prevent="processForm">
              <label for="industry" class="d-block mb-3">
                Please choose the industry that best applies to your
                organization:
              </label>
              <v-select
                id="industry"
                :items="items"
                label="Industry segment"
                v-model="industry"
              ></v-select>
              <div class="text-right">
                <ButtonPrimary type="submit" display="inline"
                  >Next</ButtonPrimary
                >
              </div>
            </form>
          </v-col>
        </v-row>
      </v-container>
    </div>
  </div>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'AssessmentCreate',

  data: () => ({
    items: ['Foo', 'Bar', 'Fizz', 'Buzz'],
    industry: null,
  }),

  methods: {
    processForm: function () {
      console.log('form submitted: ', this.industry)
    },
  },

  components: {
    ButtonPrimary,
  },
}
</script>
