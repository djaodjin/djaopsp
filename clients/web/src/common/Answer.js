import { getUniqueId } from './utils'
import Question from './Question'

export default class Answer {
  constructor({ id = getUniqueId(), question, author, frozen, answers = [] }) {
    if (!question instanceof Question) {
      throw new Error('Expecting question to be a Question instance')
    }
    this.id = id
    this.question = question
    this.author = author
    this.answers = answers
    this.frozen = frozen
  }
}
