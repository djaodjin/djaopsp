import Vue from 'vue'
import Router from 'vue-router'
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
      path: '/:org/assess/:id/',
      name: 'assessmentHome',
      component: AssessmentHome,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/assess/:id/intro/*/',
      name: 'introPractices',
      component: IntroCurrentPractices,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/assess/:id/content/*/',
      name: 'assessmentPractices',
      component: AssessmentCurrentPractices,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/targets/:id/intro/*/',
      name: 'introTargets',
      component: IntroEnvironmentalTargets,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/targets/:id/content/*/',
      name: 'assessmentTargets',
      component: AssessmentEnvironmentalTargets,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/improve/:id/intro/*/',
      name: 'introPlan',
      component: IntroImprovementPlan,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/improve/:id/content/*/',
      name: 'assessmentPlan',
      component: AssessmentImprovementPlan,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/scorecard/:id/content/*/',
      name: 'assessmentScorecard',
      component: AssessmentScorecard,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
    {
      path: '/:org/share/:id/content/*/',
      name: 'assessmentShare',
      component: AssessmentShare,
      props: true,
      pathToRegexpOptions: { strict: true },
    },
  ],
})
