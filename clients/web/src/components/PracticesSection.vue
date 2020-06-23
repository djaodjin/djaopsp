<template>
  <fragment>
    <span class="text-caption">{{ category }}</span>
    <h4>{{ title }}</h4>
    <v-container class="pa-0">
      <v-row align="center">
        <v-col class="pt-1 pb-2" cols="6">
          <v-progress-linear
            :value="completed"
            color="primary"
          ></v-progress-linear>
        </v-col>
        <v-col class="pt-1 pb-2" cols="6">
          <span class="progress-label">
            {{ answered }} / {{ questions }} questions
          </span>
        </v-col>
      </v-row>
    </v-container>
  </fragment>
</template>

<script>
export default {
  name: 'PracticesSection',

  props: ['category', 'title', 'answered', 'questions'],

  computed: {
    completed() {
      return Math.round((this.answered / this.questions) * 100)
    },
  },
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
.progress-label {
  font-size: 0.9rem;
}
</style>
