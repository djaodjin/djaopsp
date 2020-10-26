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
  base: `${process.env.VUE_APP_ROOT}${process.env.VUE_APP_CLIENT_BASE}`,
  routes: [
    {
      path: '/:org/',
      name: 'home',
      component: Home,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/create/',
      name: 'assessmentCreate',
      component: AssessmentCreate,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/home/:slug/*/',
      name: 'assessmentHome',
      component: AssessmentHome,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/assess/:slug/intro/*/',
      name: 'introPractices',
      component: IntroCurrentPractices,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/assess/:slug/*/',
      name: 'assessmentPractices',
      component: AssessmentCurrentPractices,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/targets/:slug/intro/*/',
      name: 'introTargets',
      component: IntroEnvironmentalTargets,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/targets/:slug/*/',
      name: 'assessmentTargets',
      component: AssessmentEnvironmentalTargets,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/improve/:slug/intro/*/',
      name: 'introPlan',
      component: IntroImprovementPlan,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/improve/:slug/*/',
      name: 'assessmentPlan',
      component: AssessmentImprovementPlan,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/scorecard/:slug/*/',
      name: 'assessmentScorecard',
      component: AssessmentScorecard,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/share/:slug/*/',
      name: 'assessmentShare',
      component: AssessmentShare,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
  ],
})
