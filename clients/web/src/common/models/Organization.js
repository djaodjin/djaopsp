import { getUniqueId } from '../utils'

export default class Organization {
  constructor({ id = getUniqueId(), name, assessments = [] }) {
    this.id = id
    this.name = name
    this.assessments = assessments
  }
}
