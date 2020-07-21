<template>
  <v-container :fluid="!Boolean(STANDALONE)">
    <v-row>
      <v-col>
        <component
          :is="container"
          :class="[STANDALONE ? 'standalone' : 'embedded']"
          elevation="3"
        >
          <v-row>
            <v-col>
              <h1 class="my-2 my-md-6 assessment-title">
                Environment Sustainability Assessment
              </h1>
              <div class="content">
                <p class="my-6 text-center">
                  Assess, benchmark and plan your organization's environmental
                  sustainability practices.
                </p>
                <form class="mx-md-6" @submit.prevent="processForm">
                  <label for="industry" class="d-block mb-3">
                    Please choose the industry that best applies to your
                    organization:
                  </label>
                  <v-select
                    id="industry"
                    hide-details
                    label="Industry segment"
                    v-model="industry"
                    class="mb-6"
                    :items="selectOptions"
                    :solo="Boolean(STANDALONE)"
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
                  <div v-show="industry" class="text-right">
                    <button-primary type="submit" display="inline"
                      >Next</button-primary
                    >
                  </div>
                  <div class="text-right mt-8 mb-4">
                    <span>Don't know what to select?</span>
                    <a class="ml-2" href="/docs/faq/#general-4"
                      >See examples.</a
                    >
                  </div>
                </form>
              </div>
            </v-col>
          </v-row>
        </component>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { VSheet } from 'vuetify/lib'
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
    container() {
      return this.STANDALONE ? 'div' : 'v-sheet'
    },
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
    VSheet,
    ButtonPrimary,
  },
}
</script>

<style lang="scss" scoped>
.standalone .content {
  max-width: 720px;
  margin: 0 auto;
}
.embedded {
  max-width: 720px;
  padding: 16px 24px;
  margin: 0 auto;
}
.v-list-item__title.child {
  margin-left: 16px;
}
</style>
