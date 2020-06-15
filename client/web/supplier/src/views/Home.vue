<template>
  <div class="px-4 px-sm-8">
    <h1>S1 Tamerin</h1>
    <home-actions />
  </div>
</template>

<script>
import HomeActions from '@/components/HomeActions'

export default {
  name: 'Home',

  components: {
    HomeActions,
  },
}
</script>

<style lang="scss" scoped>
h1 {
  text-align: center;
}
</style>
