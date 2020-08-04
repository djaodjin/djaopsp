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
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/assess/new/',
      name: 'newAssessment',
      component: AssessmentCreate,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/assess/:id/',
      name: 'assessmentHome',
      component: AssessmentHome,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/assess/:id/intro/:samplePath/',
      name: 'introPractices',
      component: IntroCurrentPractices,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/assess/:id/content/:samplePath/',
      name: 'assessmentPractices',
      component: AssessmentCurrentPractices,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/targets/:id/intro/:samplePath/',
      name: 'introTargets',
      component: IntroEnvironmentalTargets,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/targets/:id/content/:samplePath/',
      name: 'assessmentTargets',
      component: AssessmentEnvironmentalTargets,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/improve/:id/intro/:samplePath/',
      name: 'introPlan',
      component: IntroImprovementPlan,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/improve/:id/content/:samplePath/',
      name: 'assessmentPlan',
      component: AssessmentImprovementPlan,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/scorecard/:id/content/:samplePath/',
      name: 'assessmentScorecard',
      component: AssessmentScorecard,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/app/:org/share/:id/content/:samplePath/',
      name: 'assessmentShare',
      component: AssessmentShare,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
  ],
})
