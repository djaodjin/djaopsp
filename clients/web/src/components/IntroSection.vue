<template>
  <v-container class="mt-sm-10" tag="section">
    <v-row justify="center">
      <v-col cols="11" md="6" lg="5" tag="header" class="text-center">
        <small>Environment Sustainability Assessment</small>
        <h1 class="assessment-title">{{ title }}</h1>
      </v-col>
      <v-col cols="11" md="6" lg="5">
        <slot></slot>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'IntroSection',

  props: ['title'],
}
</script>
