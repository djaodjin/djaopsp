<template>
  <v-card class="mx-auto" max-width="340">
    <v-card-text>
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
li {
  margin-bottom: 3px;

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
</style>
