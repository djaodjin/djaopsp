<template>
  <div class="ml-4 mt-4 mb-6 ml-sm-8 mt-sm-8">
    <small>Environment Sustainability Assessment</small>
    <h1>{{ title }}</h1>
  </div>
</template>

<script>
export default {
  name: 'SectionTitle',

  props: ['title'],
}
</script>

<style lang="scss" scoped>
h1 {
  text-align: left;
  font-size: 1.2rem;
  font-weight: 500;
  margin-top: 0;
  line-height: 0.9;
}

@media #{map-get($display-breakpoints, 'sm-and-up')} {
  h1 {
    font-size: 1.8;
    line-height: 1;
  }
  small {
    font-size: 1rem;
  }
}
</style>
