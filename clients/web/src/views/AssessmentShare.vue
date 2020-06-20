<template>
  <div>
    <h3>Scorecard</h3>
    <img alt="Site logo" :src="`${publicPath}static/img/envconnect-logo.png`" />
  </div>
</template>

<script>
export default {
  name: 'assessmentShare',

  data: () => ({
    publicPath: process.env.BASE_URL,
  }),
}
</script>
