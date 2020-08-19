<template>
  <div v-bind="$attrs" class="mt-6 mb-4 mt-md-8 mb-md-6">
    <practice-group-header class="mb-2" :section="section" />
    <svg
      class="chart-practices-implementation"
      v-bind="$attrs"
      :viewBox="`0 0 ${width} ${height}`"
    >
      <g>
        <g
          class="x-axis"
          fill="none"
          :transform="`translate(${marginLeft}, ${height - marginBottom})`"
          text-anchor="middle"
        >
          <path
            class="domain"
            stroke="currentColor"
            :d="`M0,1V0.5H${width - marginLeft - 1}.5v8`"
          ></path>
          <g
            class="tick"
            opacity="1"
            text-anchor="middle"
            v-for="(bar, index) in bars"
            :key="index"
            :transform="`translate(${bar.x + bar.width / 2}, 0)`"
          >
            <line stroke="currentColor" y2="6"></line>
            <text font-size="13" fill="currentColor" y="13" dy="0.71em">
              {{ bar.label }}
            </text>
          </g>
          <text
            font-size="14"
            font-weight="500"
            fill="currentColor"
            :x="width / 2"
            y="35"
            dy="0.71em"
          >
            Implementation Rate
          </text>
        </g>
        <g class="y-axis" fill="none" font-size="14">
          <path
            class="domain"
            stroke="currentColor"
            stroke-width="1"
            :d="`M${marginLeft},${height - marginBottom}V1,h-8`"
          ></path>
          <text
            :x="height / 4"
            :y="height - marginBottom + 2"
            fill="currentColor"
            :transform="`rotate(-90 ${marginLeft / 2} ${
              height - marginBottom
            })`"
          >
            Number of companies
          </text>
        </g>
        <g
          v-for="(bar, index) in bars"
          :key="index"
          :transform="`translate(${marginLeft}, 0)`"
          class="bar"
          fill="none"
          text-anchor="middle"
        >
          <rect
            :fill="bar.color"
            :height="bar.height - marginBottom"
            :width="bar.width"
            :x="bar.x"
            :y="bar.y"
          ></rect>
          <text
            font-family="sans-serif"
            font-size="14"
            :fill="bar.color"
            :x="bar.x + bar.width / 2"
            :y="bar.y - 5"
          >
            {{ bar.value }}
          </text>
        </g>
        <g
          class="indicator"
          fill="none"
          font-size="14"
          text-anchor="middle"
          :transform="`translate(${marginLeft}, 0)`"
        >
          <path
            stroke-width="2"
            :stroke="indicator.color"
            :d="`M${indicator.x + indicator.width / 2},${
              height - marginBottom
            }V18`"
          ></path>
          <text
            :fill="indicator.color"
            :x="indicator.x + indicator.width / 2"
            :y="indicator.y + 10"
          >
            You
          </text>
        </g>
      </g>
    </svg>
  </div>
</template>

<script>
import { scaleLinear, scaleBand, scaleOrdinal } from 'd3-scale'
import { PRACTICE_VALUES } from '@/config/app'
import PracticeGroupHeader from '@/components/PracticeGroupHeader'

const CHART_TOP_OFFSET = 6

export default {
  name: 'ChartPracticesImplementation',

  props: {
    section: {
      type: Object,
      default: function () {
        return {}
      },
    },
    scores: {
      type: Array,
      default: function () {
        return []
      },
    },
    companyScore: { default: 0 },
    height: { default: 260 },
    width: { default: 500 },
    marginLeft: { default: 30 },
    marginBottom: { default: 50 },
    barPadding: { default: 0.4 },
  },

  computed: {
    sortedScores() {
      return this.scores.slice().sort((a, b) => a.value < b.value)
    },
    values() {
      // Add padding to make sure bars won't reach the top;
      // number of companies will go over each bar
      return this.sortedScores.map((d) => d.number + CHART_TOP_OFFSET)
    },
    x() {
      return scaleBand()
        .domain(this.sortedScores.map((d) => d.label))
        .range([0, this.width - this.marginLeft])
        .padding(this.barPadding)
    },
    y() {
      return scaleLinear()
        .domain([0, Math.max(...this.values)])
        .range([this.height - this.marginBottom, 0])
    },
    color() {
      return scaleOrdinal(PRACTICE_VALUES.map((p) => p.color))
    },
    bars() {
      return this.sortedScores.map((d, i) => {
        return {
          label: d.label,
          x: this.x(d.label),
          y: this.y(d.number),
          width: this.x.bandwidth(),
          height: this.height - this.y(d.number),
          color: this.color(i),
          value: d.number,
        }
      })
    },
    indicator() {
      const scoreIndex = this.sortedScores.findIndex(
        (d) => this.companyScore < d.value
      )
      const bucket = this.sortedScores[scoreIndex]
      const color =
        ((scoreIndex + 1) / this.sortedScores.length) * 10 > 5
          ? '#2ad22f' // green
          : '#d2412a' // red
      return {
        x: this.x(bucket.label),
        y: this.y(Math.max(...this.values)),
        width: this.x.bandwidth(),
        color,
      }
    },
  },

  components: {
    PracticeGroupHeader,
  },
}
</script>
