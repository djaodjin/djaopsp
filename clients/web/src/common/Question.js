import { VALID_QUESTION_TYPES } from '../config'
import { getUniqueId } from './utils'

export default class Question {
  constructor(
    section,
    subcategory,
    text,
    type,
    placeholder = '',
    optional = false
  ) {
    if (!VALID_QUESTION_TYPES.includes(type)) {
      throw new Error('Invalid question type')
    }
    this.id = getUniqueId()
    this.section = section
    this.subcategory = subcategory
    this.text = text
    this.type = type
    this.placeholder = placeholder
    this.optional = optional
  }
}
