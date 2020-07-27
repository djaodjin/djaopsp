import { getUniqueId } from './utils'

export default class Target {
  constructor({
    id = getUniqueId(),
    category,
    text,
    deadlineDate,
    baselineDate,
  }) {
    this.id = id
    this.category = category
    this.text = text
    this.deadlineDate = deadlineDate
    this.baselineDate = baselineDate
  }
}
