<template>
  <div>
    <dl>
      <dt>Industry</dt>
      <dd>
        <b>Engineering, Procurement, Construction</b>
      </dd>
      <dt>Created</dt>
      <dd>
        <time datetime="2020-06-15 10:34">June 15, 2020</time>
      </dd>
      <dt>Author</dt>
      <dd>scott@tamerinsolutions.com</dd>
    </dl>
    <div v-if="isClickable">
      <router-link :to="{ name: 'assessmentHome', params: { id: '123' } }">
        Continue:
        <b>Establish Current Practices</b>
      </router-link>
    </div>
    <div v-else>
      <span>
        Status:
        <b>Establish Current Practices</b>
      </span>
    </div>
  </div>
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
