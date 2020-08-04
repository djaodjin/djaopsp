<template>
  <h3 v-bind="$attrs" class="ma-4"><slot></slot></h3>
</template>

<script>
export default {
  name: 'SheetTitle',
}
</script>

<style lang="scss" scoped>
h3 {
  font-weight: 500;
  line-height: 1;
}
</style>
