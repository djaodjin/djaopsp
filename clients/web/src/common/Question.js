import { VALID_QUESTION_TYPES } from '@/config/app'
import { getUniqueId } from './utils'

export default class Question {
  constructor({
    id = getUniqueId(),
    path,
    section,
    subcategory,
    text,
    type,
    placeholder = 'Comments (optional)',
    optional = false,
    previousAnswers = [],
  }) {
    if (!VALID_QUESTION_TYPES.includes(type.toString())) {
      throw new Error('Invalid question type')
    }
    this.id = id
    this.path = path
    this.section = section
    this.subcategory = subcategory
    this.text = text
    this.type = type
    this.placeholder = placeholder
    this.optional = optional
    this.previousAnswers = previousAnswers
  }
}
