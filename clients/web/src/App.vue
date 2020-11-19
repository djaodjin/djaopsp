<template>
  <v-app id="tsp-supplier" :class="[STANDALONE ? 'standalone' : 'embedded']">
    <div v-if="this.$route.name === 'home' || $vuetify.breakpoint.smAndUp">
      <v-app-bar app clipped-left v-if="STANDALONE">
        <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
        <v-toolbar-title>
          <v-img
            class="d-inline-block mr-3"
            contain
            height="24"
            width="44"
            alt
            :style="{ verticalAlign: 'text-bottom' }"
            :src="`${publicPath}/static/img/envconnect-logo.png`"
          />
          <span>{{ $t('app.title') }}</span>
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <locale-changer />
      </v-app-bar>

      <v-navigation-drawer v-model="drawer" app clipped v-if="STANDALONE">
        <nav-drawer />
      </v-navigation-drawer>
    </div>

    <v-main>
      <router-view />
    </v-main>

    <div v-if="this.$route.name === 'home' && STANDALONE">
      <v-footer min-height="4rem">
        <v-col cols="12" class="text-center">
          &copy; {{ new Date().getFullYear() }} All rights reserved.
          <a
            class="d-inline-block ml-1"
            href="https://djaodjin.com/"
            target="_blank"
            >DjaoDjin inc.</a
          >
        </v-col>
      </v-footer>
    </div>

    <div
      v-if="this.$route.name !== 'home' && $vuetify.breakpoint.xs && STANDALONE"
    >
      <v-bottom-navigation app :value="mobileActiveBtn" grow dark>
        <v-btn :to="{ name: 'home', params: { org: $route.params.org } }">
          <span>Home</span>
          <v-icon>mdi-home</v-icon>
        </v-btn>

        <v-btn
          v-if="
            this.$route.name !== 'home' &&
            this.$route.name !== 'assessmentHome' &&
            this.$route.name !== 'newAssessment' &&
            this.$route.params.pathMatch
          "
          :to="
            $routeMap.get('assessmentHome').getPath({
              org: $route.params.org,
              slug: $route.params.slug,
              industryPath: $route.params.pathMatch,
            })
          "
        >
          <span>Assessment</span>
          <v-icon>mdi-map</v-icon>
        </v-btn>

        <v-btn>
          <span>Help</span>
          <v-icon>mdi-help-circle</v-icon>
        </v-btn>
      </v-bottom-navigation>
    </div>
  </v-app>
</template>

<script>
import LocaleChanger from '@/components/LocaleChanger'
import NavDrawer from '@/components/NavDrawer'

export default {
  name: 'App',

  data: () => ({
    drawer: null,
    mobileActiveBtn: null,
    publicPath: process.env.VUE_APP_ASSETS_URL || process.env.VUE_APP_ROOT,
    STANDALONE: process.env.VUE_APP_STANDALONE,
  }),

  components: {
    LocaleChanger,
    NavDrawer,
  },
}
</script>

<style lang="scss">
@import '@/styles/app.scss';

#tsp-supplier {
  &.standalone {
    background: $background-standalone;
  }
  &.embedded {
    background: transparent;
  }

  ul {
    padding: 0;
  }

  a:hover {
    text-decoration: none;
  }

  .theme--light.v-app-bar.v-toolbar.v-sheet {
    background-color: $background-toolbar;
  }
  .theme--dark.v-bottom-navigation {
    background-color: $primary-color;
  }

  .theme--light.v-sheet--outlined {
    border: thin solid rgba(100, 100, 100, 0.14);
  }
  .theme--light.v-divider {
    border-color: rgba(101, 101, 101, 0.16);
  }
}
</style>
