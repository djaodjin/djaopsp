<template>
  <header>
    <v-btn :ripple="false" text color="primary" :to="linkTo" exact>
      <v-icon small>mdi-arrow-up-circle</v-icon>
      <span class="link-text">{{ linkText }}</span>
    </v-btn>
    <h1>{{ text }}</h1>
  </header>
</template>

<script>
export default {
  name: 'HeaderPrimary',

  props: ['linkText', 'linkTo', 'text'],
}
</script>

<style lang="scss" scoped>
header {
  background: transparent;
  text-align: center;
  margin-bottom: 20px;
  color: inherit;

  .link-text {
    text-transform: none;
    font-size: 1.3rem;
    font-weight: 500;
    margin-left: 4px;
  }

  h1 {
    font-size: 1.4rem;
    font-weight: 500;
    margin-top: 0;
    line-height: 1;
  }

  @media #{map-get($display-breakpoints, 'sm-and-up')} {
    margin-top: 16px;
    margin-bottom: 32px;

    h1 {
      font-size: 1.8rem;
    }
  }

  @media #{map-get($display-breakpoints, 'md-and-up')} {
    .link-text {
      margin-left: 8px;
      font-size: 1.5rem;
    }
    h1 {
      line-height: 1.4;
    }
  }
}
</style>
