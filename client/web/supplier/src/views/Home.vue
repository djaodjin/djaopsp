<template>
  <div>
    <v-navigation-drawer v-model="drawer" app clipped>
      <nav-drawer />
    </v-navigation-drawer>

    <v-app-bar app clipped-left>
      <v-app-bar-nav-icon @click.stop="drawer = !drawer"></v-app-bar-nav-icon>
      <v-toolbar-title>TSP / Suppliers</v-toolbar-title>
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
import HomeActions from '../components/HomeActions'
import NavDrawer from '../components/NavDrawer'

export default {
  name: 'Home',

  data: () => ({
    drawer: null,
  }),

  components: {
    HomeActions,
    NavDrawer,
  },
}
</script>
