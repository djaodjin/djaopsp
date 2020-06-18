<template>
  <v-app id="tsp-supplier">
    <div v-if="this.$route.name === 'home' || $vuetify.breakpoint.smAndUp">
      <v-app-bar app clipped-left>
        <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
        <v-toolbar-title>
          <v-img
            class="d-inline-block mr-3"
            contain
            height="24"
            width="44"
            alt
            style="vertical-align: text-bottom;"
            src="./assets/images/tsp-logo.png"
          />
          <span>{{ $t('app.title') }}</span>
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <locale-changer />
      </v-app-bar>

      <v-navigation-drawer v-model="drawer" app clipped>
        <nav-drawer />
      </v-navigation-drawer>
    </div>

    <v-main>
      <router-view />
    </v-main>

    <div v-if="this.$route.name === 'home'">
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

    <div v-if="this.$route.name !== 'home' && $vuetify.breakpoint.xs">
      <v-bottom-navigation app :value="mobileActiveBtn" grow dark>
        <v-btn :to="{ name: 'home' }">
          <span>Home</span>
          <v-icon>mdi-home</v-icon>
        </v-btn>

        <v-btn
          v-if="
            this.$route.name === 'introPractices' ||
            this.$route.name === 'introTargets' ||
            this.$route.name === 'introPlan' ||
            this.$route.name === 'assessmentScorecard' ||
            this.$route.name === 'assessmentShare'
          "
          :to="{ name: 'assessmentHome', params: { id: '123' } }"
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
  }),

  mounted() {
    console.log(this.$route.path)
  },

  components: {
    LocaleChanger,
    NavDrawer,
  },
}
</script>

<style lang="scss">
@import '@/styles/app.scss';
</style>
