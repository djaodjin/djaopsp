import Vue from 'vue'
import Router from 'vue-router'
import AssessmentCreate from './views/AssessmentCreate'
import AssessmentHome from './views/AssessmentHome'
import AssessmentScorecard from './views/AssessmentScorecard'
import AssessmentShare from './views/AssessmentShare'
import Home from './views/Home'
import IntroCurrentPractices from './views/IntroCurrentPractices'
import IntroEnvironmentalTargets from './views/IntroEnvironmentalTargets'
import IntroImprovementPlan from './views/IntroImprovementPlan'

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
      path: '/assessment/:id/practices',
      name: 'introPractices',
      component: IntroCurrentPractices,
    },
    {
      path: '/assessment/:id/targets',
      name: 'introTargets',
      component: IntroEnvironmentalTargets,
    },
    {
      path: '/assessment/:id/plan',
      name: 'introPlan',
      component: IntroImprovementPlan,
    },
    {
      path: '/assessment/:id/scorecard',
      name: 'assessmentScorecard',
      component: AssessmentScorecard,
    },
    {
      path: '/assessment/:id/share',
      name: 'assessmentShare',
      component: AssessmentShare,
    },
  ],
})
