<template>
  <v-card class="mx-auto assessment-info">
    <v-card-text class="pa-md-5">
      <ul>
        <li>
          <span>Industry:</span>
          <b>Engineering, Procurement, Construction, Cows</b>
        </li>
        <li>
          <span>Created:</span>
          <time datetime="2020-06-15 10:34">June 15, 2020</time>
        </li>
        <li>
          <span>Author:</span>
          <em>scott@tamerinsolutions.com</em>
        </li>
        <li v-if="isClickable">
          <router-link :to="{ name: 'assessmentHome', params: { id: '123' } }">
            <span>Continue:</span>
            <b>Establish Current Practices</b>
          </router-link>
        </li>
        <li v-else>
          <span>Status:</span>
          <b>Establish Current Practices</b>
        </li>
      </ul>
    </v-card-text>
  </v-card>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'AssessmentInfo',

  data: () => ({
    isClickable: false,
  }),
}
</script>

<style lang="scss" scoped>
.assessment-info {
  max-width: 340px;

  @media #{map-get($display-breakpoints, 'md-and-up')} {
    max-width: 100%;
  }

  li {
    margin-bottom: 3px;

    @media #{map-get($display-breakpoints, 'md-and-up')} {
      font-size: 1rem;
      margin-bottom: 5px;
    }

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
