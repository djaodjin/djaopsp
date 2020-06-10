<template>
  <v-list dense>
    <v-list-item link>
      <v-list-item-action>
        <v-icon>mdi-compass</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>Projects</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-item link>
      <v-list-item-action>
        <v-icon>mdi-cog</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>Settings</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-item link>
      <v-list-item-action>
        <v-icon>mdi-help-circle</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>Help</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-item link>
      <v-list-item-action>
        <v-icon>mdi-exit-to-app</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>Sign out</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
  </v-list>
</template>

<script>
export default {
  name: 'NavDrawer',
}
</script>
