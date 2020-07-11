<template>
  <v-btn
    v-on="$listeners"
    :to="to"
    :block="!display || display !== 'inline'"
    :type="!type ? 'button' : type"
    :color="!color ? 'secondary' : color"
    large
    outlined
  >
    <slot></slot>
  </v-btn>
</template>

<script>
export default {
  name: 'ButtonPrimary',
  props: ['color', 'to', 'display', 'type'],
}
</script>
