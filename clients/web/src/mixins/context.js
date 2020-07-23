import Vue from 'vue'
import { getAssessment } from '../mocks/assessments'
import { getOrganization } from '../mocks/organizations'

Vue.mixin({
  beforeCreate() {
    const { context, parent } = this.$options
    if (context && context instanceof Context) {
      this.$context = context
    } else if (parent && parent.$context) {
      this.$context = parent.$context
    } else {
      console.warn(
        'Application has no $context property. Inject context instance into the Vue app constructor.'
      )
    }
  },
})

export default class Context {
  constructor() {
    this.organizations = new Map()
    this.assessments = new Map()
    this.industries = []
  }

  async getAssessment(id) {
    if (this.assessments.has(id)) {
      return this.assessments.get(id)
    } else {
      const assessment = await getAssessment(id)
      this.assessments.set(id, assessment)
      return assessment
    }
  }

  getIndustries() {
    return this.industries
  }

  async getOrganization(id) {
    if (this.organizations.has(id)) {
      return this.organizations.get(id)
    } else {
      const organization = await getOrganization(id)
      this.organizations.set(id, organization)
      return organization
    }
  }
}
