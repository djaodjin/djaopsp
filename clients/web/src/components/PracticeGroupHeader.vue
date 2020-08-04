<template>
  <v-subheader v-bind="$attrs">
    <img
      class="d-inline-block"
      height="48"
      width="48"
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
  border-radius: 3px;
  padding: 3px;
  background-color: $background-icon;
}
</style>
