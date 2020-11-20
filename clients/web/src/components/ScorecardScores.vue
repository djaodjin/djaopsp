<template>
  <v-sheet elevation="3">
    <v-container class="scores px-0">
      <v-row>
        <v-col cols="12">
          <chart-scores
            :width="200"
            :height="100"
            :topScore="92"
            :averageScore="72"
            :ownScore="58"
          />
        </v-col>
      </v-row>
      <v-row v-for="(item, index) in sortedScores" :key="index">
        <v-col cols="5" class="py-2">
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
          <span
            :class="[
              item.owner ? 'my-score' : 'other-score',
              'text-subtitle-1',
            ]"
          >
            {{ item.score }}%
          </span>
        </v-col>
        <v-col v-if="item.owner" cols="5" class="py-1 px-2">
          <div class="score-quality" v-if="item.isValid">
            <v-icon large color="green">mdi-check-decagram</v-icon>
            <span class="text-caption">Valid<br />industry score</span>
          </div>
          <div class="score-quality" v-else>
            <v-icon large color="red">mdi-cancel</v-icon>
            <span class="text-caption">Invalid<br />industry score</span>
          </div>
        </v-col>
      </v-row>
    </v-container>
  </v-sheet>
</template>

<script>
import ChartScores from '@/components/ChartScores'

export default {
  name: 'ScorecardScores',

  props: {
    scores: {
      type: Object,
      default: function () {
        return {}
      },
    },
  },

  computed: {
    sortedScores() {
      if (Object.keys(this.scores).length === 0) return []
      const { top, own, average, isValid } = this.scores
      const sorted = [
        {
          owner: false,
          title: 'Top Score',
          score: top,
        },
      ]
      const unsorted = [
        {
          owner: false,
          title: 'Average Score',
          score: average,
        },
        {
          owner: true,
          title: 'Your Score',
          score: own,
          isValid,
        },
      ]
      if (own < average) {
        sorted.push(unsorted[0])
        sorted.push(unsorted[1])
      } else {
        sorted.push(unsorted[1])
        sorted.push(unsorted[0])
      }
      return sorted
    },
  },

  components: {
    ChartScores,
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

.other-score,
.my-score {
  display: block;
  flex: 1;
  text-align: center;
}

.other-score {
  font-size: 1.2rem !important;
}

.my-score {
  font-size: 1.4rem !important;
  font-weight: 600;
}

.score-quality {
  display: flex;

  .text-caption {
    display: inline-block;
    line-height: 1.4;
    padding-left: 6px;
    padding-top: 2px;
  }
}
</style>
