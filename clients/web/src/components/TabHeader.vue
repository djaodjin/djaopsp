<template>
  <h3 class="pt-5 pl-4" v-if="$vuetify.breakpoint.smAndUp">
    {{ text }}
  </h3>
</template>

<script>
export default {
  name: 'TabHeader',

  props: ['text'],
}
</script>

<style lang="scss" scoped>
h3 {
  font-size: 1.5rem;
  font-weight: 500;
}
</style>
