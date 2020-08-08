import { VALID_QUESTION_TYPES } from '@/config/app'
import { getUniqueId } from './utils'
import Section from './Section'
import Subcategory from './Subcategory'
import Answer from './Answer'

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
    answers = [],
  }) {
    if (!VALID_QUESTION_TYPES.includes(type.toString())) {
      throw new Error('Invalid question type')
    }
    const currentAnswers = answers
      .filter((answer) => !answer.frozen)
      .map((answer) => new Answer({ ...answer, question: this }))
    if (currentAnswers.length > 1) {
      throw new Error(
        `Question at path ${path} has more than one current answer`
      )
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
    this.previousAnswers = answers
      .filter((answer) => answer.frozen)
      .map((answer) => new Answer({ ...answer, question: this }))
    this.currentAnswer = currentAnswers[0]
  }
}
