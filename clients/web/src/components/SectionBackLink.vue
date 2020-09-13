<template>
  <v-btn
    data-cy="back-link"
    class="mb-1 mb-md-6 mt-md-2"
    v-bind="$attrs"
    text
    color="primary"
  >
    <v-icon class="mr-2" small color="primary">mdi-arrow-left</v-icon>
    <span>Back</span>
  </v-btn>
</template>

<script>
export default {
  name: 'SectionBackLink',
}
</script>
