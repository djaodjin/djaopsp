import { getUniqueId } from './utils'
import { PRACTICE_VALUES, PRACTICE_VALUE_CATEGORIES } from '@/config/app'

const MIN_PRACTICE_VALUE = PRACTICE_VALUES[0].value
const values = PRACTICE_VALUE_CATEGORIES.map((c) => c.value)

export default class Practice {
  constructor({ id, question, implementationRate = 0, ...rest }) {
    this.id = id || getUniqueId()
    this.question = question
    this.implementationRate = implementationRate
    values.forEach((v) => {
      this[v] = rest[v] || MIN_PRACTICE_VALUE
    })
  }
}
