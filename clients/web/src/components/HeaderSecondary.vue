<template>
  <header v-bind="$attrs" :class="[STANDALONE ? 'standalone' : 'embedded']">
    <component :is="container" elevation="5">
      <v-btn
        class="back-btn pt-1 px-2 px-md-4"
        text
        color="primary"
        exact
        :min-height="44"
        :ripple="false"
        :to="{ name: 'assessmentHome', params: { id: $route.params.id } }"
      >
        <div class="flex-line">
          <v-icon small>mdi-arrow-up-circle</v-icon>
          <span class="ml-1 ml-md-2 link-text">{{ orgName }}</span>
        </div>
        <span class="block-line link-text">{{ industryName }}</span>
      </v-btn>
      <h1>{{ title }}</h1>
    </component>
  </header>
</template>

<script>
import { VSheet } from 'vuetify/lib'

export default {
  name: 'HeaderSecondary',

  props: ['intro', 'orgName', 'industryName', 'title'],

  data() {
    return {
      STANDALONE: process.env.VUE_APP_STANDALONE,
    }
  },

  computed: {
    container() {
      return this.STANDALONE || this.intro ? 'div' : 'v-sheet'
    },
  },

  components: {
    VSheet,
  },
}
</script>

<style lang="scss" scoped>
header {
  background: transparent;
  text-align: center;
  color: inherit;

  .back-btn {
    display: block;
  }

  ::v-deep .v-btn__content {
    display: block;
  }

  .flex-line {
    display: flex;
    justify-content: center;
    width: 100%;
  }

  .block-line {
    display: block;
    width: 100%;
  }

  .link-text {
    text-transform: none;
    font-size: 0.9rem;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    letter-spacing: -0.1px;
  }

  h1 {
    font-size: 1.4rem;
    font-weight: 500;
    margin-top: 0;
    line-height: 1;
  }

  @media #{map-get($display-breakpoints, 'sm-and-up')} {
    &.container {
      position: relative;
      padding-top: 0;
      padding-bottom: 0;

      &.standalone {
        top: 16px;

        > div {
          padding: 12px 0;
        }
      }

      &.embedded {
        > div {
          padding: 8px 0;
        }
      }
    }
  }

  @media #{map-get($display-breakpoints, 'md-and-up')} {
    &.container {
      &.embedded > div {
        padding: 12px 0 4px;
      }
    }
    .block-line {
      margin-top: 2px;
    }
    .link-text {
      font-size: 1rem;
    }
    h1 {
      font-size: 1.8rem;
      line-height: 1.6;
    }
  }
}
</style>
