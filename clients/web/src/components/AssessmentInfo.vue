<template>
  <v-card v-bind="$attrs" class="mx-auto assessment-info">
    <v-card-text class="pa-4 pt-md-6 pb-md-5">
      <ul class="pa-0">
        <li>
          <span>Industry:</span>
          <b>{{ assessment.industryName }}</b>
        </li>
        <li>
          <span>Created:</span>
          <time :datetime="assessment.created">{{ assessment.created }}</time>
        </li>
        <li>
          <span>Author:</span>
          <em>{{ assessment.authorEmail }}</em>
        </li>
        <li v-if="isClickable">
          <router-link
            :to="{ name: 'assessmentHome', params: { id: assessment.id } }"
          >
            <span>Continue:</span>
            <b>{{ ASSESSMENT_STEPS[assessment.status].text }}</b>
          </router-link>
        </li>
        <li v-else>
          <span>Status:</span>
          <b>{{ ASSESSMENT_STEPS[assessment.status].text }}</b>
        </li>
      </ul>
    </v-card-text>
  </v-card>
</template>

<script>
import { ASSESSMENT_STEPS } from '@/config/app'
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
    }
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
      width: 20%;
      text-align: right;
      vertical-align: top;

      & + * {
        display: inline-block;
        width: 78%;
        text-align: left;
      }
    }
  }
  em {
    font-style: normal;
  }
}
</style>
