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
      path: '/app/:org/',
      name: 'home',
      component: Home,
    },
    {
      path: '/app/:org/new-assessment',
      name: 'newAssessment',
      component: AssessmentCreate,
    },
    {
      path: '/app/:org/assessment/:id',
      name: 'assessmentHome',
      component: AssessmentHome,
    },
    {
      path: '/app/:org/assessment/:id/practices/intro',
      name: 'introPractices',
      component: IntroCurrentPractices,
    },
    {
      path: '/app/:org/assessment/:id/practices',
      name: 'assessmentPractices',
      component: AssessmentCurrentPractices,
    },
    {
      path: '/app/:org/assessment/:id/targets/intro',
      name: 'introTargets',
      component: IntroEnvironmentalTargets,
    },
    {
      path: '/app/:org/assessment/:id/targets',
      name: 'assessmentTargets',
      component: AssessmentEnvironmentalTargets,
    },
    {
      path: '/app/:org/assessment/:id/plan/intro',
      name: 'introPlan',
      component: IntroImprovementPlan,
    },
    {
      path: '/app/:org/assessment/:id/plan',
      name: 'assessmentPlan',
      component: AssessmentImprovementPlan,
    },
    {
      path: '/app/:org/assessment/:id/scorecard',
      name: 'assessmentScorecard',
      component: AssessmentScorecard,
    },
    {
      path: '/app/:org/assessment/:id/share',
      name: 'assessmentShare',
      component: AssessmentShare,
    },
  ],
})
