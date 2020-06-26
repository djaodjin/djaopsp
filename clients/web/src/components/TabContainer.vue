<template>
  <fragment>
    <div v-if="$vuetify.breakpoint.smAndUp">
      <v-container>
        <v-row>
          <v-col cols="12" md="6">
            <h3>{{ tabs[0].text }}</h3>
            <slot name="tab1"></slot>
          </v-col>
          <v-col cols="12" md="6">
            <h3>{{ tabs[1].text }}</h3>
            <slot name="tab2"></slot>
          </v-col>
        </v-row>
      </v-container>
    </div>
    <div class="pb-12" v-else>
      <v-tabs
        class="elevation-1"
        v-model="currentTab"
        background-color="primary"
        dark
        grow
      >
        <v-tab
          class="tab"
          :href="'#' + tabs[0].href"
          @click="refreshTabInURL(tabs[0].href)"
        >
          {{ tabs[0].text }}
        </v-tab>
        <v-tab
          class="tab"
          :href="'#' + tabs[1].href"
          @click="refreshTabInURL(tabs[1].href)"
        >
          {{ tabs[1].text }}
        </v-tab>

        <v-tab-item :value="tabs[0].href">
          <slot name="tab1"></slot>
        </v-tab-item>

        <v-tab-item :value="tabs[1].href">
          <slot name="tab2"></slot>
        </v-tab-item>
      </v-tabs>
    </div>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import SectionTitle from '@/components/SectionTitle'

export default {
  name: 'TabContainer',

  props: ['tabs'],

  created() {
    this.setTabFromURL()
  },

  methods: {
    setTabFromURL() {
      const hash = this.$route.hash
      const nameTab1 = this.tabs[0].href
      const nameTab2 = this.tabs[1].href

      if (hash.indexOf(nameTab1) >= 0) {
        this.currentTab = nameTab1
      } else if (hash.indexOf(nameTab2) >= 0) {
        this.currentTab = nameTab2
      }
    },
    refreshTabInURL(newTab) {
      window.location = `#${newTab}`
    },
  },

  watch: {
    $route: 'setTabFromURL',
  },

  data() {
    return {
      currentTab: this.tabs[0].href,
    }
  },

  components: {
    Fragment,
  },
}
</script>

<style lang="scss" scoped>
div ::v-deep .tab {
  font-size: 1rem;
}
</style>
