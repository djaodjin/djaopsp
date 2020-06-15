<template>
  <v-app id="tsp-supplier">
    <div v-if="this.$route.name === 'home' || $vuetify.breakpoint.smAndUp">
      <v-app-bar app clipped-left>
        <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
        <v-toolbar-title>{{ $t('app.title') }}</v-toolbar-title>
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

    <div v-if="this.$route.name !== 'home' && $vuetify.breakpoint.xs">
      <v-bottom-navigation :value="mobileActiveBtn" grow>
        <v-btn :to="{ name: 'home' }">
          <span>Home</span>
          <v-icon>mdi-home</v-icon>
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

  components: {
    LocaleChanger,
    NavDrawer,
  },
}
</script>

<style lang="scss">
@import '@/styles/app.scss';
</style>
