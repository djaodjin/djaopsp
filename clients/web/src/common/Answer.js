import { getUniqueId } from './utils'

export default class Answer {
  constructor({
    id = getUniqueId(),
    question,
    author,
    created = new Date().toISOString(),
    answers = [],
    answered = false,
  }) {
    this.id = id
    this.question = question // question ID
    this.author = author
    this.created = created
    this.answers = answers
    this.answered = answered
  }
}
