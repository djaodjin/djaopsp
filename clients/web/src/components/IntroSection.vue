<template>
  <v-container class="mt-sm-10" tag="section">
    <v-row justify="center">
      <v-col :cols="cols" md="8" xl="6">
        <v-sheet class="pa-4 pt-md-6 px-md-10 pb-md-8" elevation="2">
          <header-secondary
            class="mb-3"
            :intro="true"
            :orgName="orgName"
            :industryName="industryName"
            :title="title"
          />
          <v-row>
            <v-col>
              <slot></slot>
            </v-col>
          </v-row>
        </v-sheet>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import HeaderSecondary from '@/components/HeaderSecondary'

export default {
  name: 'IntroSection',

  props: {
    industryName: {
      type: String,
    },
    orgName: {
      type: String,
    },
    title: {
      type: String,
      required: true,
    },
    cols: {
      type: Number,
      default: 11,
    },
  },

  components: {
    HeaderSecondary,
  },
}
</script>

<style lang="scss" scoped>
header {
  background: transparent;
  color: inherit;
}
small {
  font-size: 1rem;
}
</style>
