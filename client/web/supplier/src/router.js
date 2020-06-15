import Vue from 'vue'
import Router from 'vue-router'
import AssessmentCreate from './views/AssessmentCreate'
import Home from './views/Home'
import Assess from './views/Assess'
import Scorecard from './views/Scorecard'

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: process.env.BASE_URL,
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/new-assessment',
      name: 'newAssessment',
      component: AssessmentCreate,
    },
    {
      path: '/assess',
      name: 'assess',
      component: Assess,
    },
    {
      path: '/scorecard',
      name: 'scorecard',
      component: Scorecard,
    },
  ],
})
