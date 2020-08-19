import { VALID_QUESTION_TYPES } from '@/config/app'
import { getUniqueId } from './utils'
import Section from './Section'
import Subcategory from './Subcategory'

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
  }) {
    if (!VALID_QUESTION_TYPES.includes(type.toString())) {
      throw new Error('Invalid question type')
    }
    this.id = id
    this.path = path
    this.section = section instanceof Section ? section : new Section(section)
    this.subcategory =
      subcategory instanceof Subcategory
        ? subcategory
        : new Subcategory(subcategory)
    this.text = text
    this.type = type
    this.placeholder = placeholder
    this.optional = optional
  }
}
