<template>
  <div class="assessment-container">
    <h1 class="assessment-title">Environment Sustainability Assessment</h1>
    <v-container>
      <v-row justify="center">
        <v-col cols="11" md="8" lg="6">
          <form @submit.prevent="processForm">
            <label for="industry" class="d-block mb-3">
              Please choose the industry that best applies to your organization:
            </label>
            <v-select
              id="industry"
              :items="allIndustrySegments"
              label="Industry segment"
              v-model="industry"
            ></v-select>
            <div class="text-right">
              <button-primary type="submit" display="inline"
                >Next</button-primary
              >
            </div>
          </form>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import {
  getIndustrySegments,
  getPreviousIndustrySegments,
} from '../mocks/industry-segments'
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'AssessmentCreate',

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.loading = true
      this.allIndustrySegments = await getIndustrySegments()
      this.previousIndustrySegments = await getPreviousIndustrySegments()
      this.loading = false
    },

    processForm: function () {
      this.$router.push({
        name: 'assessmentHome',
        params: { id: 123 },
      })
    },
  },

  data() {
    return {
      loading: false,
      allIndustrySegments: [],
      previousIndustrySegments: [],
      industry: null,
    }
  },

  components: {
    ButtonPrimary,
  },
}
</script>
