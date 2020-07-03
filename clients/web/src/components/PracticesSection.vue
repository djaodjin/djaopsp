<template>
  <div class="practice-section">
    <practice-section-header
      :category="section.content.name"
      :title="subcategory.content.name"
    />
    <v-container class="pa-0">
      <v-row align="center">
        <v-col class="pt-1 pb-2" cols="6">
          <v-progress-linear
            :value="completePercentage"
            color="primary"
          ></v-progress-linear>
        </v-col>
        <v-col class="pt-1 pb-2" cols="6">
          <span class="progress-label"
            >{{ numAnswered }} / {{ numQuestions }} questions</span
          >
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
import PracticeSectionHeader from '@/components/PracticeSectionHeader'

export default {
  name: 'PracticesSection',

  props: ['section', 'subcategory', 'unanswered'],

  computed: {
    numQuestions() {
      return this.subcategory.questions.length
    },
    numAnswered() {
      return this.subcategory.questions.reduce(
        (acc, question) =>
          !this.unanswered.find((q) => q.id === question.id) ? acc + 1 : acc,
        0
      )
    },
    completePercentage() {
      return this.numQuestions > 0
        ? Math.round((this.numAnswered / this.numQuestions) * 100)
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
