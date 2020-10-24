import Vue from 'vue'
import API from '@/common/api'

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

function createIndustryList(industries, previousIndustries) {
  let industryList = []

  if (previousIndustries.length) {
    industryList.push({ header: 'PREVIOUSLY SELECTED' })
    industryList = industryList.concat(previousIndustries)
    industryList.push({ divider: true })
  }
  // If previous industries exist, these entries will appear twice but the select control
  // will only render the first entries it finds (those for previous industries)
  return industryList.concat(industriesToList(industries))
}

export default class Context {
  constructor() {
    this.organizations = new Map()
    this.assessments = new Map()
    this.industries = []
  }

  async getAssessment(organization, assessmentId) {
    if (this.assessments.has(assessmentId)) {
      return this.assessments.get(assessmentId)
    } else {
      let assessment = organization.getAssessment(assessmentId)
      if (assessment && assessment.industryPath) {
        assessment = await API.getAssessmentWithData(organization, assessment)
        this.assessments.set(assessmentId, assessment)
      }
      return assessment
    }
  }

  async getIndustries(organization) {
    if (!this.industries.length) {
      const industries = await API.getIndustrySegments()
      const previousIndustries = organization.previousAssessments.map((a) => ({
        text: a.industryName,
        value: a.industryPath,
      }))
      this.industries = createIndustryList(industries, previousIndustries)
    }
    return this.industries
  }

  async getOrganization(organizationId) {
    if (this.organizations.has(organizationId)) {
      return this.organizations.get(organizationId)
    } else {
      const organization = await API.getOrganization(organizationId)
      this.organizations.set(organizationId, organization)
      return organization
    }
  }

  async setAssessmentIndustry(organizationId, assessmentId, industry) {
    const assessment = this.assessments.get(assessmentId)
    if (assessment) {
      const updated = await API.setAssessmentIndustry(
        organizationId,
        assessment,
        industry
      )
      this.assessments.set(assessment.id, updated)
      return updated
    }
  }

  updateAssessment(assessment) {
    this.assessments.set(assessment.id, assessment)
    return assessment
  }
}
