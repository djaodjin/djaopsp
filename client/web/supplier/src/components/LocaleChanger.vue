<template>
  <select v-model="$i18n.locale">
    <option v-for="(lang, i) in langs" :key="`Lang${i}`" :value="lang">{{
      lang
    }}</option>
  </select>
</template>

<script>
// Per: https://www.codeandweb.com/babeledit/tutorials/how-to-translate-your-vue-app-with-vue-i18n
export default {
  name: 'LocaleChanger',
  data() {
    return { langs: ['en', 'es'] }
  },
}
</script>
