<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="6" lg="4">
        <section class="mb-4 px-md-4">
          <p>{{ $t('home.desc-assessment') }}</p>
          <button-primary>{{ $t('home.btn-assessment') }}</button-primary>
        </section>
      </v-col>
      <v-col cols="12" md="6" lg="4">
        <section class="mb-4 px-md-4">
          <p>{{ $t('home.desc-history') }}</p>
          <button-primary>{{ $t('home.btn-history') }}</button-primary>
        </section>
      </v-col>
      <v-col cols="12" md="6" lg="4">
        <section class="mb-4 px-md-4">
          <p>{{ $t('home.desc-best-practices') }}</p>
          <button-primary>{{ $t('home.btn-best-practices') }}</button-primary>
        </section>
      </v-col>
    </v-row>
  </v-container>
</template>

<script>
import ButtonPrimary from '@/components/ButtonPrimary'

export default {
  name: 'HomeActions',

  components: {
    ButtonPrimary,
  },
}
</script>

<style lang="scss" scoped>
section {
  max-width: 600px;
  margin: 0 auto;
}
</style>
