<template>
  <div class="practice-section">
    <practice-section-header :category="category" :title="title" />
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
import PracticeSectionHeader from '@/components/PracticeSectionHeader'

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

  components: {
    PracticeSectionHeader,
  },
}
</script>

<style lang="scss" scoped>
.practice-section {
  width: 100%;
}
.progress-label {
  font-size: 0.85rem;
}
</style>
