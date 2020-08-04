<template>
  <svg
    class="chart-practice-values-aggregate"
    v-bind="$attrs"
    :viewBox="`0 0 ${width} ${height}`"
  >
    <g>
      <g
        class="x-axis"
        fill="none"
        :transform="`translate(${marginLeft}, ${height - marginBottom})`"
      >
        <path
          class="domain"
          stroke="currentColor"
          :d="`M0,1V0.5H${width - marginLeft}.5V6`"
        ></path>
        <g
          class="tick"
          opacity="1"
          font-size="10"
          font-family="sans-serif"
          text-anchor="middle"
          v-for="column in columns"
          :key="column.key"
          :transform="`translate(${
            column.bars[0].x + column.bars[0].width / 2
          }, 0)`"
        >
          <line stroke="currentColor" y2="6"></line>
          <text fill="currentColor" y="9" dy="0.71em">
            {{ column.label }}
          </text>
        </g>
      </g>
      <g class="y-axis" fill="none">
        <path
          class="domain"
          stroke="currentColor"
          stroke-width="1"
          :d="`M${marginLeft},${height - marginBottom}V0`"
        ></path>
        <text
          class="y-axis-text"
          :x="height / 3"
          :y="height - marginBottom + 3"
          fill="currentColor"
          :transform="`rotate(-90 ${marginLeft / 2} ${height - marginBottom})`"
        >
          Aggregate Value
        </text>
      </g>
      <g
        v-for="column in columns"
        :key="column.key"
        :transform="`translate(${marginLeft}, 0)`"
        class="column"
        fill="none"
      >
        <rect
          v-for="(bar, index) in column.bars"
          :fill="bar.color"
          :key="index"
          :height="height - bar.height - marginBottom"
          :width="bar.width"
          :x="bar.x"
          :y="bar.y"
        ></rect>
      </g>
    </g>
  </svg>
</template>

<script>
import { scaleLinear, scaleBand, scaleOrdinal } from 'd3-scale'
import { interpolateSpectral } from 'd3-scale-chromatic'
import {
  PRACTICE_VALUE_CATEGORIES,
  PRACTICE_VALUE_CATEGORY_DEFAULT,
} from '@/config/app'

export default {
  name: 'ChartPracticeValuesAggregate',

  props: {
    height: { default: 260 },
    width: { default: 500 },
    practices: {
      type: Array,
      default: function () {
        return []
      },
    },
    marginLeft: { default: 30 },
    marginBottom: { default: 30 },
    barPadding: { default: 0.4 },
  },

  data() {
    return {
      chartDomains: PRACTICE_VALUE_CATEGORIES.filter(
        (pv) => pv !== PRACTICE_VALUE_CATEGORY_DEFAULT
      ).map((pv) => pv),
    }
  },

  computed: {
    chartData() {
      return this.chartDomains.map((d) => {
        const key = d.value
        let baseline = 0
        let acc = 0
        return {
          items: this.practices.map((p, i, array) => {
            baseline = acc
            acc += p[key]
            return {
              baseline,
              value: acc,
              key,
            }
          }),
          key,
          label: d.text,
        }
      })
    },
    values() {
      return this.chartData.map((c) => c.items[c.items.length - 1].value)
    },
    x() {
      return scaleBand()
        .domain(this.chartData.map((d) => d.key))
        .range([0, this.width - this.marginLeft])
        .padding(this.barPadding)
    },
    y() {
      return scaleLinear()
        .domain([0, Math.max(...this.values)])
        .range([this.height - this.marginBottom, 0])
    },
    columns() {
      return this.chartData.map((c) => {
        return {
          label: c.label,
          bars: c.items.map((item, i, array) => ({
            x: this.x(item.key),
            y: this.y(item.value),
            width: this.x.bandwidth(),
            height: this.y(item.value - item.baseline),
            color: interpolateSpectral(i / (array.length - 1)),
          })),
        }
      })
    },
  },
}
</script>

<style lang="scss">
svg {
  .y-axis-text {
    font-size: 0.8rem;
  }
}
</style>
