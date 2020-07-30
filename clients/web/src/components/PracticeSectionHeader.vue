<template>
  <div v-bind="$attrs" :class="[small ? 'small' : 'normal', 'text-left']">
    <span v-if="section" class="text-caption">{{ section }}</span>
    <h4>{{ subcategory }}</h4>
  </div>
</template>

<script>
export default {
  name: 'PracticeSectionHeader',

  props: ['section', 'subcategory', 'small'],
}
</script>

<style lang="scss" scoped>
.small {
  .text-caption {
    line-height: 1.2;
    display: block;
  }
  h4 {
    font-size: 1rem;
    font-weight: 600;
    margin-top: 2px;
    margin-bottom: 4px;
  }
}
.normal {
  .text-caption {
    display: block;
    line-height: 1.8;
    font-weight: 600;

    @media #{map-get($display-breakpoints, 'md-and-up')} {
      font-size: 0.9rem !important;
      font-weight: 500;
    }
  }
  h4 {
    font-size: 1.3rem;
    font-weight: 500;
    margin-top: 0;
    line-height: 1.2;
  }
}
</style>
