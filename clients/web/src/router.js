import Vue from 'vue'
import Router from 'vue-router'
import AssessmentCreate from './views/AssessmentCreate'
import AssessmentCurrentPractices from './views/AssessmentCurrentPractices'
import AssessmentEnvironmentalTargets from './views/AssessmentEnvironmentalTargets'
import AssessmentHome from './views/AssessmentHome'
import AssessmentImprovementPlan from './views/AssessmentImprovementPlan'
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
      path: '/assessment/:id/practices/intro',
      name: 'introPractices',
      component: IntroCurrentPractices,
    },
    {
      path: '/assessment/:id/practices',
      name: 'assessmentPractices',
      component: AssessmentCurrentPractices,
    },
    {
      path: '/assessment/:id/targets/intro',
      name: 'introTargets',
      component: IntroEnvironmentalTargets,
    },
    {
      path: '/assessment/:id/targets',
      name: 'assessmentTargets',
      component: AssessmentEnvironmentalTargets,
    },
    {
      path: '/assessment/:id/plan/intro',
      name: 'introPlan',
      component: IntroImprovementPlan,
    },
    {
      path: '/assessment/:id/plan',
      name: 'assessmentPlan',
      component: AssessmentImprovementPlan,
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
