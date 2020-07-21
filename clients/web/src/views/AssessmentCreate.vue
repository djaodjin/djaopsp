<template>
  <v-container :class="[STANDALONE ? 'standalone' : 'embedded']">
    <v-row>
      <v-col>
        <h1 class="my-2 my-md-6 assessment-title">
          Environment Sustainability Assessment
        </h1>
      </v-col>
    </v-row>
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <p class="text-center">
          Assess, benchmark and plan your organization's environmental
          sustainability practices.
        </p>
        <form class="mx-2 mx-md-6" @submit.prevent="processForm">
          <label for="industry" class="d-block mb-3"
            >Please choose the industry that best applies to your
            organization:</label
          >
          <v-select
            id="industry"
            :items="selectOptions"
            label="Industry segment"
            v-model="industry"
            solo
          >
            <template v-slot:item="{ item, on, attrs }">
              <v-list-item-content v-bind="attrs" v-on="on">
                <v-list-item-title
                  :class="[item.isChild ? 'child' : 'single']"
                  v-text="item.text"
                ></v-list-item-title>
              </v-list-item-content>
            </template>
          </v-select>
          <div v-show="industry" class="text-right mb-8">
            <button-primary type="submit" display="inline">
              Next
            </button-primary>
          </div>
          <div class="text-right">
            <span>Don't know what to select?</span>
            <a class="ml-2" href="/docs/faq/#general-4">See examples.</a>
          </div>
        </form>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { postAssessment } from '../mocks/assessments'
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
      this.allIndustrySegments = await getIndustrySegments()
      this.previousIndustrySegments = await getPreviousIndustrySegments()
    },

    processForm: function () {
      // TODO: Post new assessment; then redirect to the assessment home page
      // TODO: How to get the author information?
      postAssessment().then((newAssessment) => {
        this.$router.push({
          name: 'assessmentHome',
          params: { id: newAssessment.id },
        })
      })
    },
  },

  data() {
    return {
      allIndustrySegments: [],
      previousIndustrySegments: [],
      industry: null,
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  computed: {
    selectOptions() {
      return [
        {
          header: 'PREVIOUSLY SELECTED',
        },
        ...this.previousIndustrySegments.map((i) => ({ ...i, isChild: true })),
        { divider: true },
        ...this.allIndustrySegments,
      ]
    },
  },

  components: {
    ButtonPrimary,
  },
}
</script>

<style lang="scss" scoped>
.embedded h1 {
  color: white;
}
.v-list-item__title.child {
  margin-left: 16px;
}
</style>
