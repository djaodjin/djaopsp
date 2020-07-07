<template>
  <v-container class="scores px-0 pt-0">
    <v-row v-for="(item, index) in sortedScores" :key="index">
      <v-col cols="5" class="pa-2">
        <span
          :class="[
            item.owner ? 'my-score-label' : 'score-label',
            'text-body-1',
          ]"
        >
          {{ item.title }}
        </span>
      </v-col>
      <v-col cols="2" class="pa-2">
        <span :class="[item.owner ? 'my-score' : 'score', 'text-subtitle-1']">
          {{ item.score }}%
        </span>
      </v-col>
      <v-col v-if="item.isValid" cols="5" class="pa-2">
        <span class="text-body-1">
          {{ item.isValid }}
        </span>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
export default {
  name: 'ScorecardScores',

  props: ['scores'],

  computed: {
    sortedScores() {
      if (!this.scores) return []
      const sorted = [
        {
          owner: false,
          title: 'Top Score',
          score: this.scores.top,
        },
      ]
      const unsorted = [
        {
          owner: false,
          title: 'Average Score',
          score: this.scores.average,
        },
        {
          owner: true,
          title: 'Your Score',
          score: this.scores.own.score,
          isValid: this.scores.own.isValid,
        },
      ]
      if (this.scores.own.score < this.scores.average) {
        sorted.push(unsorted[0])
        sorted.push(unsorted[1])
      } else {
        sorted.push(unsorted[1])
        sorted.push(unsorted[0])
      }
      return sorted
    },
  },
}
</script>

<style lang="scss" scoped>
.score-label,
.my-score-label {
  display: block;
  flex: 1;
  text-align: right;
}

.score-label {
  padding-top: 1px;
}

.my-score-label {
  padding-top: 2px;
  font-weight: 600;
}

.score,
.my-score {
  display: block;
  flex: 1;
  text-align: center;
}

.score {
  font-size: 1.2rem !important;
}

.my-score {
  font-size: 1.4rem !important;
  font-weight: 600;
}
</style>
