import Vue from 'vue'
import Router from 'vue-router'
import AssessmentCreate from '@/views/AssessmentCreate'
import AssessmentCurrentPractices from '@/views/AssessmentCurrentPractices'
import AssessmentEnvironmentalTargets from '@/views/AssessmentEnvironmentalTargets'
import AssessmentHome from '@/views/AssessmentHome'
import AssessmentImprovementPlan from '@/views/AssessmentImprovementPlan'
import AssessmentScorecard from '@/views/AssessmentScorecard'
import AssessmentShare from '@/views/AssessmentShare'
import History from '@/views/History'
import Home from '@/views/Home'
import IntroCurrentPractices from '@/views/IntroCurrentPractices'
import IntroEnvironmentalTargets from '@/views/IntroEnvironmentalTargets'
import IntroImprovementPlan from '@/views/IntroImprovementPlan'
import { template } from '@/common/utils'

class AppView {
  constructor({ name, routeFn, routePlaceholders, component }) {
    this.name = name
    this.path = routeFn(routePlaceholders)
    this.component = component
    this.props = true
    this.pathToRegexpOptions = { strict: true }
    this.getPath = routeFn
  }
}

export const routeMap = new Map([
  [
    'home',
    new AppView({
      routeFn: template`/${'org'}/`,
      routePlaceholders: { org: ':org' },
      component: Home,
    }),
  ],
  [
    'introPractices',
    new AppView({
      routeFn: template`/${'org'}/assess/${'slug'}/intro/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: IntroCurrentPractices,
    }),
  ],
  [
    'assessmentPractices',
    new AppView({
      routeFn: template`/${'org'}/assess/${'slug'}/content/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: AssessmentCurrentPractices,
    }),
  ],
  [
    'assessmentHome',
    new AppView({
      routeFn: template`/${'org'}/assess/${'slug'}/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: AssessmentHome,
    }),
  ],
  [
    'assessmentCreate',
    new AppView({
      routeFn: template`/${'org'}/assess/`,
      routePlaceholders: { org: ':org' },
      component: AssessmentCreate,
    }),
  ],
  [
    'introTargets',
    new AppView({
      routeFn: template`/${'org'}/targets/${'slug'}/intro/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: IntroEnvironmentalTargets,
    }),
  ],
  [
    'assessmentTargets',
    new AppView({
      routeFn: template`/${'org'}/targets/${'slug'}/content/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: AssessmentEnvironmentalTargets,
    }),
  ],
  [
    'introPlan',
    new AppView({
      routeFn: template`/${'org'}/improve/${'slug'}/intro/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: IntroImprovementPlan,
    }),
  ],
  [
    'assessmentPlan',
    new AppView({
      routeFn: template`/${'org'}/improve/${'slug'}/content/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: AssessmentImprovementPlan,
    }),
  ],
  [
    'assessmentScorecard',
    new AppView({
      routeFn: template`/${'org'}/scorecard/${'slug'}/content/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: AssessmentScorecard,
    }),
  ],
  [
    'assessmentShare',
    new AppView({
      routeFn: template`/${'org'}/share/${'slug'}/content/${'industryPath'}/`,
      routePlaceholders: { org: ':org', slug: ':slug', industryPath: '*' },
      component: AssessmentShare,
    }),
  ],
  [
    'history',
    new AppView({
      routeFn: template`/${'org'}/history/`,
      routePlaceholders: { org: ':org' },
      component: History,
    }),
  ],
])

Vue.mixin({
  beforeCreate() {
    const { routeMap, parent } = this.$options
    if (routeMap && routeMap instanceof Map) {
      this.$routeMap = routeMap
    } else if (parent && parent.$routeMap) {
      this.$routeMap = parent.$routeMap
    } else {
      console.warn(
        'Application has no $routeMap property. Inject routeMap into the Vue app constructor.'
      )
    }
  },
})

Vue.use(Router)

export default new Router({
  mode: 'history',
  base: `${process.env.VUE_APP_ROOT}${process.env.VUE_APP_CLIENT_BASE}`,
  routes: Array.from(routeMap).map(([key, value]) => ({
    ...value,
    name: key,
  })),
})
