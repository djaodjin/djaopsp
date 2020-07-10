<template>
  <div>
    <span class="text-caption">{{ section }}</span>
    <h4>{{ subcategory }}</h4>
  </div>
</template>

<script>
export default {
  name: 'PracticeSectionHeader',

  props: ['section', 'subcategory'],
}
</script>

<style lang="scss" scoped>
.text-caption {
  font-weight: 600;
}
h4 {
  font-size: 1.3rem;
  font-weight: 500;
  margin-top: 0;
  line-height: 1;
}
</style>
