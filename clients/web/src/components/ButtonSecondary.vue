<template>
  <v-btn
    v-on="$listeners"
    :to="to"
    :block="!display || display !== 'inline'"
    :type="!type ? 'button' : type"
    large
    outlined
    color="secondary"
  >
    <slot></slot>
  </v-btn>
</template>

<script>
export default {
  name: 'ButtonPrimary',
  props: ['to', 'display', 'type'],
}
</script>
