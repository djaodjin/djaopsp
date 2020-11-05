<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <component
          :is="container"
          :class="[STANDALONE ? 'standalone' : 'embedded']"
          elevation="3"
        >
          <section-back-link
            :to="
              $routeMap.get('home').getPath({
                org,
              })
            "
            exact
          />
          <div
            data-cy="history-table"
            v-if="
              organization.previousAssessments &&
              organization.previousAssessments.length
            "
          >
            <p class="my-4">
              The following assessments have been completed by your
              organization:
            </p>
            <v-data-table
              class="assessment-history"
              hide-default-footer
              must-sort
              :sort-by="['created']"
              :sort-desc="[true]"
              :headers="headers"
              :items="organization.previousAssessments"
              :items-per-page="organization.previousAssessments.length"
            >
              <template v-slot:item.created="{ item, value }">
                <time :datetime="value" v-format-date>{{ value }}</time>
              </template>
              <template v-slot:item.slug="{ item, value }">
                <router-link
                  :to="
                    $routeMap.get('assessmentScorecard').getPath({
                      org,
                      slug: value,
                      industryPath: item.industryPath,
                    })
                  "
                >
                  View scorecard
                </router-link>
              </template>
            </v-data-table>
          </div>
          <div
            class="pa-6"
            v-else-if="
              organization.previousAssessments &&
              !organization.previousAssessments.length
            "
          >
            <p data-cy="empty-placeholder" class="text-subtitle-1 text-center">
              The organization does not have any archived assessments.<br />
              Any assessments completed over 6 months ago will be listed in this
              section.
            </p>
          </div>
        </component>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import { VSheet } from 'vuetify/lib'
import { formatDate } from '@/directives'
import ButtonPrimary from '@/components/ButtonPrimary'
import SectionBackLink from '@/components/SectionBackLink'

export default {
  name: 'History',

  props: ['org'],

  created() {
    this.fetchData()
  },

  methods: {
    async fetchData() {
      this.organization = await this.$context.getOrganization(this.org)
    },
  },

  data() {
    return {
      organization: {},
      STANDALONE: process.env.VUE_APP_STANDALONE,
      headers: [
        {
          text: 'Completed',
          value: 'created',
        },
        { text: 'Industry Segment', value: 'industryName' },
        {
          text: 'Overall Score',
          value: 'score',
        },
        {
          text: 'Scorecard',
          value: 'slug',
        },
      ],
    }
  },

  directives: {
    formatDate,
  },

  computed: {
    container() {
      return this.STANDALONE ? 'div' : 'v-sheet'
    },
  },

  components: {
    ButtonPrimary,
    SectionBackLink,
    VSheet,
  },
}
</script>

<style lang="scss" scoped>
.assessment-history.v-data-table {
  border-radius: 3px;

  & ::v-deep table > thead > tr:last-child > th {
    border-color: #cacaca;
  }
  & ::v-deep .v-data-table__wrapper > table > tbody > tr:not(:last-child) > td {
    border-color: #efefef;
  }
}
.embedded {
  padding: 16px 20px;
}
</style>
