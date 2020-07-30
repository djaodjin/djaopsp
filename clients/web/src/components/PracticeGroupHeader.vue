<template>
  <v-subheader class="mt-2 mb-4">
    <img
      class="d-inline-block"
      height="46"
      width="46"
      alt
      :src="section.content.iconPath"
    />
    <span class="ml-4">{{ section.content.name }}</span>
  </v-subheader>
</template>

<script>
export default {
  name: 'PracticeGroupHeader',

  props: ['section'],
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

span {
  text-transform: uppercase;
  font-weight: 500;
}
img {
  padding: 2px;
  background-color: $background-icon;
}
</style>
