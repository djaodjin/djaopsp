<template>
  <select v-model="$i18n.locale" @change="onChange($event)">
    <option v-for="(lang, i) in langs" :key="`Lang${i}`" :value="lang">
      {{ lang }}
    </option>
  </select>
</template>

<script>
// Per: https://www.codeandweb.com/babeledit/tutorials/how-to-translate-your-vue-app-with-vue-i18n
export default {
  name: 'LocaleChanger',
  data() {
    return { langs: ['en', 'es'] }
  },
  methods: {
    onChange(event) {
      // Change vuetify's locale
      this.$vuetify.lang.current = event.target.value
    },
  },
}
</script>
