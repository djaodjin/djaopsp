<template>
  <v-container class="mt-sm-10" tag="section">
    <v-row justify="center">
      <v-col :cols="cols" md="8" lg="6">
        <v-sheet class="py-3 pb-4 px-6 pt-md-6 px-md-10 pb-md-8" elevation="2">
          <v-row>
            <v-col tag="header" class="text-center">
              <small>Environment Sustainability Assessment</small>
              <h1 class="assessment-title">{{ title }}</h1>
            </v-col>
          </v-row>
          <v-row>
            <v-col>
              <slot></slot>
            </v-col>
          </v-row>
        </v-sheet>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'IntroSection',

  props: {
    title: {
      type: String,
      required: true,
    },
    cols: {
      type: Number,
      default: 11,
    },
  },
}
</script>

<style lang="scss" scoped>
header {
  background: transparent;
  color: inherit;
}
small {
  font-size: 1rem;
}
</style>
