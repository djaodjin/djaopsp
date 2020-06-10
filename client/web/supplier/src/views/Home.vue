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
      <hello-world />
    </v-content>
  </div>
</template>

<script>
import HelloWorld from '../components/HelloWorld'
import NavDrawer from '../components/NavDrawer'

export default {
  name: 'Home',

  data: () => ({
    drawer: null,
  }),

  components: {
    HelloWorld,
    NavDrawer,
  },
}
</script>
