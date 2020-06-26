<template>
  <div>
    <span class="text-caption">{{ category }}</span>
    <h4>{{ title }}</h4>
  </div>
</template>

<script>
// TODO: Rename category to 'section' and title to 'subcategory'
export default {
  name: 'PracticeSectionHeader',

  props: ['category', 'title'],
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
