<template>
  <svg class="chart-scores" v-bind="$attrs" :viewBox="`0 0 ${width} ${height}`">
    <!-- top score arc -->
    <g :transform="`translate(0, ${height})`">
      <path
        id="topScorePath"
        fill="none"
        :d="`m ${baseWidth} 0 a 
          ${radiusOuterAngle * angleDecreaseCoeffient} ${
          radiusOuterAngle * angleDecreaseCoeffient
        } 0 0 1 ${width - baseWidth * 2} 0`"
      />
      <path
        class="arc-score"
        :style="`transform: rotate(${topScoreRotation}deg);`"
        :fill="highColor"
        :d="`m 0 0 a 
          ${radiusOuterAngle} ${radiusOuterAngle} 0 0 1 ${width} 0 l -${baseWidth} 0 a ${
          radiusOuterAngle * angleDecreaseCoeffient
        } ${radiusOuterAngle * angleDecreaseCoeffient} 0 0 0 -${
          width - baseWidth * 2
        } 0 z`"
      />
      <text
        class="score-label"
        :x="`${textXOffset}`"
        :dy="`-${textYOffset}`"
        fill="white"
      >
        <textPath href="#topScorePath">top score ({{ topScore }}%)</textPath>
      </text>
    </g>

    <!-- average score arc -->
    <g :transform="`translate(0, ${height})`">
      <path
        id="averageScorePath"
        fill="none"
        :d="`m ${baseWidth * 2} 0 a 
          ${radiusOuterAngle * angleDecreaseCoeffient} ${
          radiusOuterAngle * angleDecreaseCoeffient
        } 0 0 1 ${width - baseWidth * 4} 0`"
      />
      <path
        class="arc-score"
        :style="`transform: rotate(${averageScoreRotation}deg);`"
        :fill="mediumColor"
        :d="`m ${baseWidth} 0 a 
          ${radiusOuterAngle * angleDecreaseCoeffient} ${
          radiusOuterAngle * angleDecreaseCoeffient
        } 0 0 1 ${width - baseWidth * 2} 0 l -${baseWidth} 0 a ${
          radiusOuterAngle * angleDecreaseCoeffient
        } ${radiusOuterAngle * angleDecreaseCoeffient} 0 0 0 -${
          width - baseWidth * 4
        } 0  z`"
      />
      <text
        class="score-label"
        :x="`${textXOffset}`"
        :dy="`-${textYOffset}`"
        fill="white"
      >
        <textPath href="#averageScorePath">
          average ({{ averageScore }}%)
        </textPath>
      </text>
    </g>

    <!-- own score arc -->
    <g :transform="`translate(0, ${height})`">
      <path
        id="ownScorePath"
        fill="none"
        :d="`m ${baseWidth * 3} 0 a 
          ${radiusOuterAngle * angleDecreaseCoeffient} ${
          radiusOuterAngle * angleDecreaseCoeffient
        } 0 0 1 ${width - baseWidth * 6} 0`"
      />
      <path
        class="arc-score"
        :style="`transform: rotate(${ownScoreRotation}deg);`"
        :fill="lowColor"
        :d="`m ${baseWidth * 2} 0 a 
          ${radiusOuterAngle * angleDecreaseCoeffient} ${
          radiusOuterAngle * angleDecreaseCoeffient
        } 0 0 1 ${width - baseWidth * 4} 0 l -${baseWidth} 0 a ${
          radiusOuterAngle * angleDecreaseCoeffient
        } ${radiusOuterAngle * angleDecreaseCoeffient} 0 0 0 -${
          width - baseWidth * 6
        } 0  z`"
      />
      <text
        class="score-label"
        :x="`${textXOffset}`"
        :dy="`-${textYOffset}`"
        fill="white"
      >
        <textPath href="#ownScorePath">you ({{ ownScore }}%)</textPath>
      </text>
    </g>
    <g class="counter" :transform="`translate(${width / 2}, ${height})`">
      <text dx="-1.6rem" dy="-5">{{ counterValue }}%</text>
    </g>
  </svg>
</template>

<script>
import { PRACTICE_VALUES } from '@/config/app'

function percentageToRotation(percentage) {
  return (percentage / 100) * 180 + 180
}

const ROTATION_ANIMATION_DELAY = 1000
const COUNTER_ANIMATION_LENGTH = ROTATION_ANIMATION_DELAY + 800

export default {
  name: 'ChartScores',

  props: {
    height: { default: 156 },
    width: { default: 290 },
    topScore: { type: Number },
    averageScore: { type: Number },
    ownScore: { type: Number },
  },

  mounted() {
    this.$nextTick(
      function () {
        // Code that will run only after the entire view has been rendered
        setTimeout(() => {
          this.topScoreRotation = percentageToRotation(this.topScore)
          this.averageScoreRotation = percentageToRotation(this.averageScore)
          this.ownScoreRotation = percentageToRotation(this.ownScore)
        }, ROTATION_ANIMATION_DELAY)

        const tickDuration = COUNTER_ANIMATION_LENGTH / this.ownScore

        const counterAnimation = (counter, limit) => {
          if (counter <= limit) {
            this.counterValue = counter
            this.$nextTick((_this) => {
              // Ensure the DOM has been updated before the next counter increase
              setTimeout(
                function () {
                  counterAnimation(counter + 1, limit)
                }.bind(_this),
                tickDuration
              )
            })
          }
        }
        counterAnimation(0, this.ownScore)
      }.bind(this)
    )
  },

  data() {
    return {
      baseSegments: 12,
      angleDecreaseCoeffient: 0.5,
      textXOffset: 4,
      textYOffset: 5,
      lowColor: PRACTICE_VALUES[0].color,
      mediumColor: PRACTICE_VALUES[1].color,
      highColor: PRACTICE_VALUES[2].color,
      topScoreRotation: 180,
      averageScoreRotation: 180,
      ownScoreRotation: 180,
      counterValue: 0,
    }
  },

  computed: {
    baseWidth() {
      return this.width / this.baseSegments
    },
    radiusOuterAngle() {
      return this.width / 2
    },
  },
}
</script>

<style lang="scss">
svg {
  .counter {
    font-size: 2.2rem;
    font-family: Courier, monospace;
    font-weight: 400;
  }
  .arc-score {
    transform-origin: top center;
    transition: transform 0.8s ease-in-out;
  }
  .score-label {
    font-size: 0.8rem;
    font-family: 'Roboto', sans-serif !important;
  }
}
</style>
