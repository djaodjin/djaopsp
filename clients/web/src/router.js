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
      path: '/app/:org/home/:id',
      name: 'assessmentHome',
      component: AssessmentHome,
    },
    {
      path: '/app/:org/assess/:id/sample/:samplePath/intro',
      name: 'introPractices',
      component: IntroCurrentPractices,
      props: true,
    },
    {
      path: '/app/:org/assess/:id/sample/:samplePath',
      name: 'assessmentPractices',
      component: AssessmentCurrentPractices,
    },
    {
      path: '/app/:org/targets/:id/sample/:samplePath/intro',
      name: 'introTargets',
      component: IntroEnvironmentalTargets,
      props: true,
    },
    {
      path: '/app/:org/targets/:id/sample/:samplePath',
      name: 'assessmentTargets',
      component: AssessmentEnvironmentalTargets,
    },
    {
      path: '/app/:org/improve/:id/sample/:samplePath/intro',
      name: 'introPlan',
      component: IntroImprovementPlan,
      props: true,
    },
    {
      path: '/app/:org/improve/:id/sample/:samplePath',
      name: 'assessmentPlan',
      component: AssessmentImprovementPlan,
    },
    {
      path: '/app/:org/scorecard/:id/sample/:samplePath',
      name: 'assessmentScorecard',
      component: AssessmentScorecard,
      props: true,
    },
    {
      path: '/app/:org/share/:id/share/:samplePath',
      name: 'assessmentShare',
      component: AssessmentShare,
    },
  ],
})
