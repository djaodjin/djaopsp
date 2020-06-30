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
    this._id = getUniqueId()
    this._section = section
    this._subcategory = subcategory
    this._text = text
    this._type = type
    this._placeholder = placeholder
    this._optional = optional
  }

  get section() {
    return this._section
  }

  get subcategory() {
    return this._subcategory
  }

  get text() {
    return this._text
  }

  get type() {
    return this._type
  }

  get placeholder() {
    return this._placeholder
  }

  get optional() {
    return this._optional
  }
}
