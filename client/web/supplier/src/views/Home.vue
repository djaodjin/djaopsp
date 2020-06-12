<template>
  <div>
    <v-navigation-drawer v-model="drawer" app clipped>
      <nav-drawer />
    </v-navigation-drawer>

    <v-app-bar app clipped-left>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>{{ $t('app.title') }}</v-toolbar-title>
      <v-spacer></v-spacer>
      <locale-changer />
    </v-app-bar>

    <v-content>
      <div class="px-4 px-sm-8">
        <h1>S1 Tamerin</h1>
        <home-actions />
      </div>
    </v-content>
  </div>
</template>

<script>
import HomeActions from '@/components/HomeActions'
import LocaleChanger from '@/components/LocaleChanger'
import NavDrawer from '@/components/NavDrawer'

export default {
  name: 'Home',

  data: () => ({
    drawer: null,
  }),

  components: {
    HomeActions,
    LocaleChanger,
    NavDrawer,
  },
}
</script>
