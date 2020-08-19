import { getUniqueId } from './utils'
import Organization from './Organization'
import Assessment from './Assessment'
import Question from './Question'

export default class Answer {
  constructor({
    id = getUniqueId(),
    organization,
    assessment,
    question,
    author,
    frozen = false,
    answers = [],
    answered = false,
  }) {
    this.id = id
    this.organization = organization // organization ID
    this.assessment = assessment // assessment ID
    this.question = question // question ID
    this.author = author
    this.answers = answers
    this.frozen = frozen
    this.answered = answered
  }
}
