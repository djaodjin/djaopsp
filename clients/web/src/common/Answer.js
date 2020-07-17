export default class Answer {
  constructor({
    questionId,
    questionType,
    author,
    answers = [],
    modified = new Date(),
  }) {
    this.questionId = questionId
    this.questionType = questionType
    this.author = author
    this.answers = answers
    this.modified = modified
  }
}
