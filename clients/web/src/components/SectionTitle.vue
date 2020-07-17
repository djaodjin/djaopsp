<template>
  <div class="ma-4 ml-sm-8 mt-sm-8">
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
  small {
    font-size: 1rem;
  }
  h1 {
    font-size: 1.8rem;
    line-height: 1;
  }
}

@media #{map-get($display-breakpoints, 'md-and-up')} {
  small {
    display: block;
    font-size: 1.2rem;
    text-align: center;
  }
  h1 {
    line-height: 1.2;
    text-align: center;
  }
}
</style>
