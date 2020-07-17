<template>
  <div class="charts">
    <img alt src="../assets/images/chart-management.png" />
    <img alt src="../assets/images/chart-construction.png" />
    <img alt src="../assets/images/chart-eng-and-design.png" />
    <img alt src="../assets/images/chart-office-grounds.png" />
    <img alt src="../assets/images/chart-procurement.png" />
  </div>
</template>

<script>
export default {
  name: 'BusinessComparison',
}
</script>

<style lang="scss" scoped>
.charts {
  @media #{map-get($display-breakpoints, 'sm-and-up')} {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-around;
  }

  img {
    display: block;
    width: 260px;
    height: 185px;
    margin: 30px auto;

    @media #{map-get($display-breakpoints, 'sm-and-up')} {
      margin: 20px;
    }
  }
}
</style>
