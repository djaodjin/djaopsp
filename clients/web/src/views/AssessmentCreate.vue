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
              <header-primary
                :linkText="organization.name"
                :linkTo="{ name: 'home' }"
                text="Environment Sustainability Assessment"
              />
              <div class="content">
                <p class="my-6 text-center">
                  Assess, benchmark and plan your organization's environmental
                  sustainability practices.
                </p>
                <form class="mx-md-6" @submit.prevent="processForm">
                  <label
                    data-cy="industry-label"
                    for="industry"
                    class="d-block mb-3"
                  >
                    Please choose the industry that best applies to your
                    organization:
                  </label>
                  <v-select
                    id="industry"
                    hide-details
                    label="Industry segment"
                    v-model="industry"
                    class="mb-6"
                    :items="industries"
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
                    <a
                      data-cy="examples"
                      class="ml-2"
                      href="/docs/faq/#general-4"
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
import { createAssessment } from '@/common/api'
import ButtonPrimary from '@/components/ButtonPrimary'
import HeaderPrimary from '@/components/HeaderPrimary'

export default {
  name: 'AssessmentCreate',

  props: ['org'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      const [organization, industries] = await Promise.all([
        this.$context.getOrganization(this.org),
        this.$context.getIndustries(),
      ])
      this.organization = organization
      this.industries = industries
    },

    processForm: function () {
      // TODO: How to get the author information?
      createAssessment({ industry: this.industry }).then((newAssessment) => {
        this.$router.push({
          name: 'assessmentHome',
          params: { id: newAssessment.id },
        })
      })
    },
  },

  data() {
    return {
      organization: {},
      industries: [],
      industry: null,
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  computed: {
    container() {
      return this.STANDALONE ? 'div' : 'v-sheet'
    },
  },

  components: {
    VSheet,
    ButtonPrimary,
    HeaderPrimary,
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
