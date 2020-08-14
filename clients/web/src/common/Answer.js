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
    if (!organization instanceof Organization) {
      throw new Error('Expecting organization to be an Organization instance')
    }
    if (!assessment instanceof Assessment) {
      throw new Error('Expecting assessment to be an Assessment instance')
    }
    if (!question instanceof Question) {
      throw new Error('Expecting question to be a Question instance')
    }
    this.id = id
    this.organization = organization
    this.assessment = assessment
    this.question = question
    this.author = author
    this.answers = answers
    this.frozen = frozen
    this.answered = answered
  }
}
