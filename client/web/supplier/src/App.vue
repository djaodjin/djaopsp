<template>
  <div id="supplier-app">
    <div id="nav">
      <router-link to="/">Home</router-link>&nbsp;|
      <router-link to="/learn">Learn</router-link>&nbsp;|
      <router-link to="/assess">Assess</router-link>&nbsp;|
      <router-link to="/scorecard">Scorecard</router-link>
    </div>
    <router-view />
  </div>
</template>

<style lang="scss">
#supplier-app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  padding-bottom: 10px;
}
#nav {
  padding: 30px;
  a {
    font-weight: bold;
    color: #2c3e50;
    &.router-link-exact-active {
      color: #42b983;
    }
  }
}
</style>
