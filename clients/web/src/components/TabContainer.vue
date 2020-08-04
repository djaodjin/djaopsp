<template>
  <div v-bind="$attrs">
    <div v-if="$vuetify.breakpoint.smAndUp">
      <v-container>
        <v-row>
          <v-col
            cols="12"
            :md="mdColumnLeft"
            :lg="lgColumnLeft"
            :xl="xlColumnLeft"
          >
            <v-sheet class="mx-2 mb-3 mx-lg-auto" elevation="3">
              <slot name="tab1"></slot>
            </v-sheet>
          </v-col>
          <v-col
            v-if="!rightColHidden"
            cols="12"
            :md="mdColumnRight"
            :lg="lgColumnRight"
            :xl="xlColumnRight"
          >
            <v-sheet class="mx-2 mb-3 mx-lg-auto" elevation="3">
              <slot name="tab2"></slot>
            </v-sheet>
          </v-col>
        </v-row>
      </v-container>
    </div>
    <div v-else>
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
          @click="refreshURL(tabs[0].href)"
        >
          <slot name="tab1.title">{{ tabs[0].text }}</slot>
        </v-tab>
        <v-tab
          class="tab"
          :href="'#' + tabs[1].href"
          @click="refreshURL(tabs[1].href)"
        >
          <slot name="tab2.title">{{ tabs[1].text }}</slot>
        </v-tab>

        <v-tab-item :value="tabs[0].href">
          <slot name="tab1"></slot>
        </v-tab-item>

        <v-tab-item :value="tabs[1].href">
          <slot name="tab2"></slot>
        </v-tab-item>
      </v-tabs>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TabContainer',

  props: {
    tabs: {
      type: Array,
      required: true,
    },
    rightColHidden: {
      type: Boolean,
      default: false,
    },
    mdCol: {
      type: Number,
      default: 12,
    },
    mdLeftCol: {
      type: Number,
    },
    mdRightCol: {
      type: Number,
    },
    lgCol: {
      type: Number,
      default: 12,
    },
    lgLeftCol: {
      type: Number,
    },
    lgRightCol: {
      type: Number,
    },
    xlCol: {
      type: Number,
      default: 12,
    },
    xlLeftCol: {
      type: Number,
    },
    xlRightCol: {
      type: Number,
    },
  },

  computed: {
    mdColumnLeft() {
      return this.mdLeftCol || this.mdCol
    },
    mdColumnRight() {
      return this.mdRightCol || this.mdCol
    },
    lgColumnLeft() {
      return this.lgLeftCol || this.lgCol
    },
    lgColumnRight() {
      return this.lgRightCol || this.lgCol
    },
    xlColumnLeft() {
      return this.xlLeftCol || this.xlCol
    },
    xlColumnRight() {
      return this.xlRightCol || this.xlCol
    },
  },

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
    refreshURL(newTab) {
      // Remove any query params so they will not cause any conflicts
      // when switching tabs
      this.$router.replace(`${this.$route.path}#${newTab}`)
    },
  },

  data() {
    return {
      currentTab: this.tabs[0].href,
    }
  },
}
</script>

<style lang="scss" scoped>
div ::v-deep .tab {
  font-size: 1rem;
}
</style>
