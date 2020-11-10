<template>
  <v-list>
    <v-list-item
      link
      :to="{ name: 'home', params: { org: $route.params.org } }"
      exact
    >
      <v-list-item-action>
        <v-icon>mdi-home</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>{{ $t('nav.opt-home') }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-item
      v-if="
        $route.name !== 'home' &&
        $route.name !== 'assessmentHome' &&
        $route.name !== 'newAssessment' &&
        $route.params.pathMatch
      "
      link
      :to="
        $routeMap.get('assessmentHome').getPath({
          org: $route.params.org,
          slug: $route.params.slug,
          industryPath: $route.params.pathMatch,
        })
      "
      exact
    >
      <v-list-item-action>
        <v-icon>mdi-map</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>{{ $t('nav.opt-assessment') }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-item link>
      <v-list-item-action>
        <v-icon>mdi-compass</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>{{ $t('nav.opt-projects') }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-item link>
      <v-list-item-action>
        <v-icon>mdi-cog</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>{{ $t('nav.opt-settings') }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-item link>
      <v-list-item-action>
        <v-icon>mdi-help-circle</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>{{ $t('nav.opt-help') }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
    <v-list-item link>
      <v-list-item-action>
        <v-icon>mdi-exit-to-app</v-icon>
      </v-list-item-action>
      <v-list-item-content>
        <v-list-item-title>{{ $t('nav.opt-sign-out') }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
  </v-list>
</template>

<script>
export default {
  name: 'NavDrawer',
}
</script>
