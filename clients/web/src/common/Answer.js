import { getUniqueId } from './utils'

export default class Answer {
  constructor({
    id = getUniqueId(),
    question,
    author,
    answers = [],
    answered = false,
  }) {
    this.id = id
    this.question = question // question ID
    this.author = author
    this.answers = answers
    this.answered = answered
  }
}
