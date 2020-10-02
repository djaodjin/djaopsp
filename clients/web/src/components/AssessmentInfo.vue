<template>
  <v-card
    v-bind="$attrs"
    class="mx-auto assessment-info"
    :outlined="!Boolean(STANDALONE)"
  >
    <v-card-text class="pa-4 pt-md-6 pb-md-5">
      <ul class="pa-0">
        <li v-if="assessment.industryName" data-cy="industry-name">
          <span>Industry:</span>
          <b>{{ assessment.industryName }}</b>
        </li>
        <li>
          <span>Last updated:</span>
          <time v-format-date :datetime="assessment.created">{{
            assessment.created
          }}</time>
        </li>
        <!-- TODO: Replace with list of contributors
        <li>
          <span>Author:</span>
          <em>{{ assessment.authorEmail }}</em>
        </li> -->
        <li v-if="isClickable">
          <router-link
            :to="{ name: 'assessmentHome', params: { id: assessment.id } }"
          >
            <b class="status" v-if="assessment.frozen">Completed</b>
            <b class="status" v-else>In Progress</b>
          </router-link>
        </li>
        <li v-else>
          <b class="status" v-if="assessment.frozen">Completed</b>
          <b class="status" v-else>In Progress</b>
        </li>
      </ul>
    </v-card-text>
  </v-card>
</template>

<script>
import { ASSESSMENT_STEPS } from '@/config/app'
import { formatDate } from '@/directives'
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'AssessmentInfo',

  props: {
    assessment: {
      type: Object,
      require: true,
    },
    isClickable: {
      type: Boolean,
      default: false,
    },
  },

  data() {
    return {
      ASSESSMENT_STEPS,
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  directives: {
    formatDate,
  },
}
</script>

<style lang="scss" scoped>
.assessment-info {
  max-width: 440px;

  li {
    font-size: 1rem;
    margin-bottom: 5px;

    span {
      display: inline-block;
      margin-right: 2%;
      width: 30%;
      text-align: right;
      vertical-align: top;

      & + * {
        display: inline-block;
        width: 68%;
        text-align: left;
      }
    }

    .status {
      margin-left: 32%;
      text-align: left;
      width: 78%;
    }
  }
  em {
    font-style: normal;
  }
}
</style>
