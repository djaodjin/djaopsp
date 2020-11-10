import { getUniqueId } from '../utils'

export default class Organization {
  constructor({
    id = getUniqueId(),
    name,
    assessments = [],
    previousAssessments = [],
  }) {
    this.id = id
    this.name = name
    this.assessments = assessments
    this.previousAssessments = previousAssessments
  }

  addAssessment(assessment) {
    this.assessments.push(assessment)
  }

  findAssessment(assessmentId) {
    return this.assessments.find((a) => a.id === assessmentId)
  }

  findPreviousAssessmentByIndustry(industryPath) {
    // We assume that previous assessments are sorted by date (descending) so
    // the first one found will be the most recent.
    return this.previousAssessments.find((a) => a.industryPath === industryPath)
  }

  replaceAssessment(assessment) {
    const index = this.assessments.findIndex((a) => a.id === assessment.id)
    this.assessments.splice(index, 1, assessment)
  }
}
