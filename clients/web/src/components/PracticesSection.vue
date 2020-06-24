<template>
  <div class="practice-section">
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
            {{ answers }} / {{ questions }} questions
          </span>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
export default {
  name: 'PracticesSection',

  props: ['category', 'title', 'answers', 'questions'],

  computed: {
    completed() {
      return this.questions > 0
        ? Math.round((this.answers / this.questions) * 100)
        : 0
    },
  },
}
</script>

<style lang="scss" scoped>
.practice-section {
  width: 100%;
}
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
  font-size: 0.85rem;
}
</style>
