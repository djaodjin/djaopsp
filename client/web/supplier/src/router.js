import Vue from 'vue'
import Router from 'vue-router'
import AssessmentCreate from './views/AssessmentCreate'
import AssessmentHome from './views/AssessmentHome'
import Home from './views/Home'
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
      path: '/assessment/:id',
      name: 'assessmentHome',
      component: AssessmentHome,
    },
    {
      path: '/scorecard',
      name: 'scorecard',
      component: Scorecard,
    },
  ],
})
