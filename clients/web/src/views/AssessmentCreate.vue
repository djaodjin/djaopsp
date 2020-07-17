<template>
  <div class="assessment-container">
    <h1 class="assessment-title">Environment Sustainability Assessment</h1>
    <v-container>
      <v-row justify="center">
        <v-col cols="11" md="8" lg="6">
          <form @submit.prevent="processForm">
            <label for="industry" class="d-block mb-3"
              >Please choose the industry that best applies to your
              organization</label
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
      this.allIndustrySegments = await getIndustrySegments()
      this.previousIndustrySegments = await getPreviousIndustrySegments()
    },

    processForm: function () {
      // TODO: Post new assessment; then redirect to the assessment home page
      this.$router.push({
        name: 'assessmentHome',
        params: { id: 123 },
      })
    },
  },

  data() {
    return {
      allIndustrySegments: [],
      previousIndustrySegments: [],
      industry: null,
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
.v-list-item__title.child {
  margin-left: 16px;
}
</style>
