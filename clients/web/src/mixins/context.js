import Vue from 'vue'
import { getAssessment, getOrganization } from '@/common/api'
import {
  getIndustrySegments,
  getPreviousIndustrySegments,
} from '../mocks/industry-segments'

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

function previousIndustriesToList(previousIndustries) {
  const results = []

  for (let i = 0, parent = null; i < previousIndustries.length; i++) {
    const entry = previousIndustries[i]
    const { path, title, indent } = entry

    if (path && indent === 0) {
      // Unset grouping parent
      if (parent) parent = null
      results.push({ text: title, value: path })
    } else if (path && indent === 1) {
      // Entry with parent
      if (!parent) {
        console.warn(`Entry ${path}: ${title} has indent=1 but no parent`)
      } else {
        results.push({
          text: `${title}`,
          value: path,
        })
      }
    } else {
      parent = entry
    }
  }
  return results
}

function industriesToList(industries) {
  const results = []

  for (let i = 0, parent = null; i < industries.length; i++) {
    const entry = industries[i]
    const { path, title, indent } = entry

    if (path && indent === 0) {
      // Unset grouping parent
      if (parent) parent = null
      results.push({ text: title, value: path })
    } else if (path && indent === 1) {
      // Entry with parent
      if (!parent) {
        console.warn(`Entry ${path}: ${title} has indent=1 but no parent`)
      } else {
        results.push({
          text: title,
          value: path,
          isChild: true,
        })
      }
    } else {
      parent = entry
      results.push({ header: entry.title.toUpperCase() })
    }
  }
  return results
}

function createIndustryList(previousIndustries, industries) {
  let industryList = []

  if (previousIndustries.length) {
    industryList.push({ header: 'PREVIOUSLY SELECTED' })
    industryList = industryList.concat(
      previousIndustriesToList(previousIndustries)
    )
    industryList.push({ divider: true })
  }
  return industryList.concat(industriesToList(industries))
}

export default class Context {
  constructor() {
    this.organizations = new Map()
    this.assessments = new Map()
    this.industries = []
  }

  async getAssessment(assessmentId) {
    if (this.assessments.has(assessmentId)) {
      return this.assessments.get(assessmentId)
    } else {
      const assessment = await getAssessment(assessmentId)
      this.assessments.set(assessmentId, assessment)
      return assessment
    }
  }

  async getIndustries() {
    if (!this.industries.length) {
      const [industries, previousIndustries] = await Promise.all([
        getIndustrySegments(),
        getPreviousIndustrySegments(),
      ])
      this.industries = createIndustryList(
        previousIndustries.results,
        industries.results
      )
    }
    return this.industries
  }

  async getOrganization(organizationId) {
    if (this.organizations.has(organizationId)) {
      return this.organizations.get(organizationId)
    } else {
      const organization = await getOrganization(organizationId)
      this.organizations.set(organizationId, organization)
      return organization
    }
  }
}
