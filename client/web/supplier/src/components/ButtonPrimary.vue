<template>
  <v-btn :depressed="$vuetify.breakpoint.xs" block large color="primary">
    <slot></slot>
  </v-btn>
</template>

<script>
export default {
  name: 'ButtonPrimary',
}
</script>
