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

  getAssessment(assessmentId) {
    return this.assessments.find((a) => a.id === assessmentId)
  }
}
