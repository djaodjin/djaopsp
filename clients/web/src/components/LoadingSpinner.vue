<template>
  <div class="spinner"></div>
</template>

<script>
export default {
  name: 'LoadingSpinner',
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.spinner {
  width: 70px;
  height: 70px;
  background-color: $primary-color;
  margin: 60% auto 0;

  border-radius: 100%;
  animation: scaleout-spinner 1s infinite ease-in-out;
}

@keyframes scaleout-spinner {
  0% {
    transform: scale(0);
  }
  100% {
    transform: scale(1);
    opacity: 0;
  }
}
</style>
